# -*- coding: utf-8 -*-
import time
import requests
import json
# 禁用HTTPS证书警告（自签名证书场景）
import yaml

requests.packages.urllib3.disable_warnings()


class GD_NacosClient:
    def __init__(self, host, port="8080", ssl=1):
        self.host = host
        self.port = port
        # 适配HTTP/HTTPS协议
        self.http = "https://" if ssl == 1 else "http://"
        # 保存登录后的token（方便后续接口调用）
        self.access_token = None

    def nacos_login(self, username="nacos", password="nacos"):
        """
        Nacos 3.1.0登录接口（v3版本API）
        :param username: Nacos用户名
        :param password: Nacos密码
        :return: 登录成功返回token，失败返回None
        """
        try:
            # 1. 修正API路径：Nacos 3.x登录接口是/nacos/v3/auth/users/login（不是user）
            url = f"{self.http}{self.host}:{self.port}/v3/auth/user/login"
            # 2. 修正headers拼写错误（heeaders -> headers）
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            json_data = {
                "username": username,
                "password": password
            }

            # 3. 发送登录请求（添加超时时间，避免卡死）
            response = requests.post(
                url=url,
                headers=headers,
                data=json_data,
                verify=False,
                timeout=10
            )
            # 非200状态码直接抛异常
            response.raise_for_status()

            # 4. 修正json()方法调用（response.json -> response.json()）
            response_json = response.json()

            # 5. 提取并保存token
            self.access_token = response_json.get("accessToken")
            if self.access_token:
                print(f"登录成功！Access Token：{self.access_token[:10]}...")
                return self.access_token
            else:
                print(f"登录失败：未获取到token，响应内容：{response_json}")
                return None

        except Exception as e:
            print(f"登录异常：{str(e)}")
            return None

    def get_config(self, data_id="QSSME-GENERAL.yaml", group="DEFAULT_GROUP", namespace="public"):
        """
        登录后获取指定配置（适配Nacos v3控制台接口）
        :param data_id: 配置ID
        :param group: 配置分组
        :param namespace: 命名空间ID
        :return: 配置内容字符串
        """
        if not self.access_token:
            print("获取配置失败：未登录，access_token为空")
            return None

        try:
            url = f"{self.http}{self.host}:{self.port}/v3/console/cs/config"
            auth_dict = {
                "accessToken": self.access_token,
                "tokenTtl": 16712,
                "globalAdmin": True,
                "username": "nacos"
            }
            headers = {
                "Accept": "application/json",
                "AccessToken": self.access_token,
                "Authorization": json.dumps(auth_dict),
                "Content-Type": "application/json"
            }
            params = {
                "dataId": data_id,
                "groupName": group,
                "tenant": namespace,
                "namespaceId": ""
            }
            response = requests.get(
                url=url,
                headers=headers,
                params=params,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            # ========== 关键修复：适配v3接口的JSON结构 ==========
            # v3接口的配置在 response_json["data"]["content"] 里
            response_json = response.json()
            data = response_json.get("data", {})  # 先取data字段
            config_content = data.get("content", "")  # 再从data里取content
            self.md5_value=data.get("md5","")
            print(f"md5:{self.md5_value}")
            if config_content:
                print(f"成功获取配置：{data_id}（长度：{len(config_content)}字符）")
                return config_content
            else:
                print(f"获取配置失败：响应中无有效配置，响应内容：{response_json}")
                return None
        except json.JSONDecodeError:
            print(f"获取配置失败：响应不是合法JSON，内容：{response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"获取配置失败：请求异常 - {str(e)}")
            return None
        except Exception as e:
            print(f"获取配置失败：未知异常 - {str(e)}")
            return None

    def publish_config(self, data_id="QSSME-GENERAL.yaml", group="DEFAULT_GROUP", new_content=""):
        """
        适配Nacos v3控制台修改接口（完全模拟浏览器请求）
        :param data_id: 配置ID
        :param group: 配置分组
        :param new_content: 新配置内容（YAML字符串）
        :return: 是否成功
        """
        if not self.access_token:
            print("[修改失败] 请先登录")
            return False

        try:
            # 1. 接口URL（与浏览器一致）
            url = f"{self.http}{self.host}:{self.port}/v3/console/cs/config?username=nacos"

            # 2. 请求头（完全复制浏览器）
            headers = {

                "AccessToken": self.access_token,
                "Casmd5":self.md5_value,  # 从浏览器请求头获取的MD5
                "Content-Type": "application/x-www-form-urlencoded",
            }
            # 3. 表单参数（与浏览器完全一致）
            form_data = {
                "dataId": data_id,
                "group": group,
                "content": new_content,
                "appName": "",
                "desc": "",
                "type": "yaml",
                "id": "987253465434869760",  # 从浏览器表单获取的配置ID
                "namespaceId": "public",
                "groupName": group,
                "md5": self.md5_value,  # 与Casmd5一致
                "createTime": str(int(time.time()*1000)),  # 从浏览器表单获取
                "modifyTime": str(int(time.time()*1000)),
                "encryptedDataKey": "",
                "createUser": "nacos",
                "createIp": "",
                "configTags": "",
                "betaIps": ""
            }
            # 4. 发送POST请求
            response = requests.post( url=url,headers=headers,data=form_data,verify=False,  timeout=10)
            response.raise_for_status()
            # 5. 解析响应（v3接口返回{"code":0,"message":"success"}为成功）
            response_json = response.json()
            if response_json.get("code") == 0 and response_json.get("message") == "success":
                print(f"[修改成功] 配置 {data_id}")
                return True
            else:
                print(f"[修改失败] 响应：{response_json}")
                return False
        except Exception as e:
            print(f"[修改异常] {str(e)}")
            return False

    def list_naming_instance(self, service_name, group_name="DEFAULT_GROUP", namespace_id="", cluster_name="DEFAULT"):
        """
        调用 Nacos 3.x 服务发现接口，获取实例列表
        :param service_name: 服务名 (例如: key-distribute)
        :param group_name: 分组名 (默认: DEFAULT_GROUP)
        :param namespace_id: 命名空间ID (默认: 空字符串代表 public)
        :param cluster_name: 集群名 (默认: DEFAULT)
        :return: 实例列表 (JSON格式) 或 None (失败时)
        """
        if not self.access_token:
            print("❌ 请先调用 nacos_login() 完成登录！")
            return None

        # Nacos 3.x 服务发现接口
        url = f"{self.http}{self.host}:{self.port}/v3/console/ns/instance/list"

        # 构建查询参数
        params = {
            "serviceName": service_name,
            "groupName": group_name,
            "namespaceId": namespace_id,
            "clusterName": cluster_name,
            "pageSize": 100,
            "pageNo": 1
        }

        # 构建请求头，使用 Bearer Token 认证
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        print(f"正在请求服务实例: {url}")
        print(f"参数: {params}")

        # 发送 GET 请求
        response = requests.get(
            url=url,
            params=params,
            headers=headers,
            verify=False,
            timeout=10
        )
        response_json = response.json()
        if response_json.get("code") == 0 and response_json.get("message") == "success":
            instances = response_json["data"]["pageItems"]
            print(f"response.json:{response_json}")
            print(f"instance:{instances}")
            # 返回解析后的 JSON 数据
            return instances
        else:
            print(f"状态码: {response.status_code}")
            print(f"错误响应内容: {response.text}")
            return response.status_code

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 初始化客户端（适配你的Nacos环境：172.16.6.20:8080，HTTPS）
    nacos = GD_NacosClient(host="172.16.6.20", port="8080", ssl=1)
    token = nacos.nacos_login(username="nacos", password="nacos")

    config_str = nacos.get_config(data_id="QSSME-GENERAL.yaml")
    print(f"配置内容预览：{config_str},类型为{type(config_str)}")
    config_yaml=yaml.load(config_str, Loader=yaml.FullLoader)
    print(f"config_yaml:{config_yaml}/n,类型为{type(config_yaml)}")

    config_yaml["default-code"]="345"
    print(f"修改后配置文件：:{config_yaml}")
    new_config_str = yaml.dump(config_yaml, allow_unicode=True)
    print(f"新配置文件是：{new_config_str},类型是{type(new_config_str)}")
    nacos.set_config(data_id="QSSME-GENERAL.yaml",new_content= new_config_str)
    nacos.list_instances(service_name="key-distribute")