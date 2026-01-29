"""
AI Agent SDK 客户端（API 模式）
包含完整的 AI 处理和数据库操作
"""
import requests
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, date
from decimal import Decimal
from .exceptions import AIAgentError, AuthenticationError, RateLimitError


class DatabaseAdapter:
    """内置数据库适配器 - 支持 MySQL"""
    
    def __init__(self, config: dict):
        self.config = config
        self._connection = None
    
    def _get_connection(self):
        import pymysql
        # 检查连接是否有效，无效则重新连接
        if self._connection is not None:
            try:
                self._connection.ping(reconnect=True)
            except:
                self._connection = None
        
        if self._connection is None:
            self._connection = pymysql.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                database=self.config.get("database", ""),
                charset=self.config.get("charset", "utf8mb4"),
                cursorclass=pymysql.cursors.DictCursor
            )
        return self._connection
    
    def execute_sql(self, sql: str) -> list:
        """执行原生SQL语句"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # 判断是SELECT还是其他操作
        if sql.strip().upper().startswith("SELECT"):
            records = cursor.fetchall()
            cursor.close()
            return list(records)
        else:
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return [{"affected_rows": affected}]
    
    def list(self, entity: str, where: dict = None, limit: int = 1000, offset: int = 0) -> tuple:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 构建基础查询
        base_sql = f"SELECT * FROM `{entity}`"
        count_sql = f"SELECT COUNT(*) as total FROM `{entity}`"
        params = []
        
        if where:
            conditions = [f"`{k}` = %s" for k in where.keys()]
            where_clause = " WHERE " + " AND ".join(conditions)
            base_sql += where_clause
            count_sql += where_clause
            params = list(where.values())
        
        # 先获取总数
        cursor.execute(count_sql, params)
        total_result = cursor.fetchone()
        total = total_result.get("total", 0) if total_result else 0
        
        # 再获取分页数据
        base_sql += f" ORDER BY id DESC LIMIT {limit} OFFSET {offset}"
        cursor.execute(base_sql, params)
        records = cursor.fetchall()
        cursor.close()
        return list(records), total
    
    def create(self, entity: str, data: dict) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        fields = ", ".join([f"`{k}`" for k in data.keys()])
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO `{entity}` ({fields}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return {"id": new_id, **data}
    
    def update(self, entity: str, id: Any, data: dict) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"`{k}` = %s" for k in data.keys()])
        sql = f"UPDATE `{entity}` SET {set_clause} WHERE id = %s"
        cursor.execute(sql, list(data.values()) + [id])
        conn.commit()
        cursor.close()
        return {"id": id, **data}
    
    def delete(self, entity: str, id: Any) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        sql = f"DELETE FROM `{entity}` WHERE id = %s"
        cursor.execute(sql, [id])
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    
    def execute(self, sql: str, params: list = None) -> list:
        """执行原始 SQL 查询"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("SHOW"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = [{"affected_rows": cursor.rowcount}]
        cursor.close()
        return list(result)
    
    def _execute_query(self, sql: str, params: tuple = None, fetch_one: bool = False, commit: bool = True):
        """执行SQL查询（兼容旧API）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        
        if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("SHOW"):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        else:
            if commit:
                conn.commit()
            result = [{"affected_rows": cursor.rowcount}]
        cursor.close()
        return result
    
    def _commit(self):
        """提交事务"""
        if self._connection:
            self._connection.commit()
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


class AIAgentClient:
    """
    AI Agent 客户端
    
    用于连接 AI Agent 服务，通过自然语言操作后台系统
    
    Example:
        >>> from ai_agent_sdk import AIAgentClient
        >>> client = AIAgentClient("your_api_key")
        >>> client.register_schema(
        ...     api_base_url="http://your-backend.com/api",
        ...     entities=[{"name": "user", "fields": [...]}]
        ... )
        >>> result = client.chat("查询所有用户")
        >>> print(result)
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://wangyunge.top",
        timeout: int = 120,
        db_config: dict = None,
        db_adapter: Any = None,
        auto_schema: bool = True
    ):
        """
        初始化客户端
        
        Args:
            api_key: API Key，从 AI Agent 平台获取
            base_url: API 服务地址，默认为官方地址
            timeout: 请求超时时间（秒）
            db_config: 数据库配置（自动创建 MySQL 适配器）
            db_adapter: 自定义数据库适配器（需实现 list/create/update/delete 方法）
            auto_schema: 是否自动从数据库生成 Schema（默认 True）
        
        Example:
            # 方式1：使用内置 MySQL 适配器
            client = AIAgentClient("ak_xxx", db_config={
                "host": "localhost",
                "user": "root",
                "password": "xxx",
                "database": "mydb"
            })
            
            # 方式2：使用自定义适配器
            client = AIAgentClient("ak_xxx", db_adapter=my_db)
        """
        if not api_key:
            raise ValueError("api_key 不能为空")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "AI-Agent-SDK/1.0.0 Python"
        })
        
        # 数据库适配器
        if db_adapter:
            self._db = db_adapter
        elif db_config:
            self._db = DatabaseAdapter(db_config)
        else:
            self._db = None
        
        # Schema 状态
        self._schema_registered = False
        self._entities = []
        self._cached_schema = None  # 缓存的 Schema
        self._schema_file = None  # Schema 文件路径
        self._conversation_id = None
        self._history = []
        self._pending_sql = {}  # 待确认的SQL（内存备用）
        self._redis = None  # Redis客户端
        self._export_dir = None  # 自定义导出目录
        self._init_redis()
        
        # 自动从数据库生成 Schema（如果有数据库连接）
        if self._db and auto_schema:
            try:
                self.generate_schema_from_db(use_ai=False)
                print("[SDK] 已自动从数据库生成 Schema")
            except Exception as e:
                print(f"[SDK] 自动生成 Schema 失败: {e}")
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            import redis
            import os
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD", "123456")
            
            self._redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True
            )
            # 测试连接
            self._redis.ping()
            print(f"[SDK] Redis连接成功: {redis_host}:{redis_port}")
        except Exception as e:
            print(f"[SDK] Redis连接失败，使用内存存储: {e}")
            self._redis = None
    
    def set_export_dir(self, export_dir: str):
        """
        设置Excel导出目录
        
        Args:
            export_dir: 导出目录路径，如果为None则使用系统临时目录
        """
        import os
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        self._export_dir = export_dir
    
    def _store_export_data(self, records: list) -> str:
        """
        存储导出数据到Redis，返回下载token
        数据在用户点击下载时才生成Excel文件
        
        Args:
            records: 要导出的数据记录
        
        Returns:
            下载token
        """
        import secrets
        import json
        from decimal import Decimal
        from datetime import datetime, date
        
        token = f"export_{secrets.token_hex(16)}"
        
        # 序列化数据
        def serialize(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        serialized = [{k: serialize(v) for k, v in r.items()} for r in records]
        data = json.dumps(serialized, ensure_ascii=False)
        
        if self._redis:
            # 存储到Redis，1小时过期
            self._redis.setex(token, 3600, data)
        else:
            # 内存存储（备用）
            if not hasattr(self, '_export_cache'):
                self._export_cache = {}
            self._export_cache[token] = serialized
        
        return token
    
    def generate_excel_from_token(self, token: str) -> str:
        """
        根据下载token生成Excel文件
        
        Args:
            token: 下载token
        
        Returns:
            生成的Excel文件路径，如果token无效返回None
        """
        import json
        
        records = None
        
        if self._redis:
            data = self._redis.get(token)
            if data:
                records = json.loads(data)
                # 下载后删除token
                self._redis.delete(token)
        else:
            if hasattr(self, '_export_cache') and token in self._export_cache:
                records = self._export_cache.pop(token)
        
        if not records:
            return None
        
        return self._export_to_excel_from_records(records)
    
    def _request(
        self, 
        method: str, 
        path: str, 
        data: dict = None,
        params: dict = None
    ) -> dict:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{path}"
        
        try:
            resp = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise AIAgentError("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise AIAgentError("无法连接到服务器，请检查网络或服务地址")
        
        # 处理错误响应
        if resp.status_code == 401:
            raise AuthenticationError("API Key 无效或已过期", status_code=401)
        elif resp.status_code == 429:
            raise RateLimitError("请求频率超限，请稍后重试", status_code=429)
        elif resp.status_code >= 400:
            try:
                error_data = resp.json()
                message = error_data.get("detail", resp.text)
            except:
                message = resp.text
            raise AIAgentError(message, status_code=resp.status_code)
        
        return resp.json()
    
    # ============ Schema 注册 ============
    
    def register_schema(
        self,
        entities: List[Dict[str, Any]],
        system_name: str = None,
        system_description: str = None,
        api_base_url: str = None
    ) -> Dict[str, Any]:
        """
        注册后台系统的 Schema
        
        告诉 AI Agent 你的后台系统有哪些实体和操作
        
        Args:
            entities: 实体列表，每个实体包含 name, fields, operations
            system_name: 系统名称，如 "学生管理系统"
            system_description: 系统描述
            api_base_url: 后台 API 基础地址（可选），如 "http://your-backend.com/api"
        
        Returns:
            dict: 注册结果
            
        Example:
            >>> client.register_schema(
            ...     api_base_url="http://my-shop.com/api",
            ...     system_name="电商管理系统",
            ...     entities=[
            ...         {
            ...             "name": "order",
            ...             "description": "订单",
            ...             "fields": [
            ...                 {"name": "id", "type": "number"},
            ...                 {"name": "customer", "type": "string"},
            ...                 {"name": "amount", "type": "number"}
            ...             ],
            ...             "operations": ["list", "get", "create", "update", "delete"]
            ...         }
            ...     ]
            ... )
            {'success': True, 'entities': ['order']}
        """
        data = {
            "api_base_url": api_base_url or "",
            "entities": entities
        }
        if system_name:
            data["system_name"] = system_name
        if system_description:
            data["system_description"] = system_description
        
        # 缓存 Schema（不再发送到 api_server）
        self._cached_schema = data
        self._schema_registered = True
        self._entities = [e["name"] if isinstance(e, dict) else e for e in entities]
        return {"success": True, "message": "Schema 已缓存"}
    
    def set_schema_file(self, file_path: str):
        """
        设置 Schema 文件路径，自动加载和保存
        
        Args:
            file_path: Schema 文件路径
        """
        import json
        from pathlib import Path
        self._schema_file = Path(file_path)
        
        # 自动加载
        if self._schema_file.exists():
            with open(self._schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
                if schema and schema.get("entities"):
                    self.register_schema(
                        entities=schema["entities"],
                        system_name=schema.get("system_name"),
                        system_description=schema.get("system_description")
                    )
    
    def save_schema_to_file(self):
        """保存当前 Schema 到文件"""
        import json
        if self._schema_file and self._cached_schema:
            with open(self._schema_file, "w", encoding="utf-8") as f:
                json.dump(self._cached_schema, f, ensure_ascii=False, indent=2)
    
    def save_and_register_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存并注册 Schema（保存到文件 + 注册到内存）
        
        Args:
            schema: Schema 配置，包含 entities, system_name 等
        
        Returns:
            dict: {"success": True, "message": "..."}
        """
        import json
        
        # 1. 注册到内存
        if schema.get("entities"):
            self.register_schema(
                entities=schema["entities"],
                system_name=schema.get("system_name"),
                system_description=schema.get("system_description")
            )
        
        # 2. 保存到文件
        if self._schema_file:
            with open(self._schema_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
            print(f"[SDK] Schema 已保存到 {self._schema_file}")
        
        return {"success": True, "message": "Schema 保存并注册成功"}
    
    def check_schema_completeness(self) -> Dict[str, Any]:
        """
        检查 Schema 完整性（字段是否都有描述）
        
        Returns:
            dict: {
                "complete": bool,  # 是否完整
                "missing_descriptions": list,  # 缺少描述的字段列表
                "message": str  # 提示信息
            }
        """
        schema = self.get_schema(auto_generate=False)
        if not schema or not schema.get("entities"):
            return {
                "complete": False,
                "missing_descriptions": [],
                "message": "Schema 未配置，请先在「表结构管理」中配置数据表"
            }
        
        missing = []
        for entity in schema.get("entities", []):
            entity_name = entity.get("name", "unknown")
            for field in entity.get("fields", []):
                field_name = field.get("name", "unknown")
                description = field.get("description", "")
                if not description or description.strip() == "":
                    missing.append(f"{entity_name}.{field_name}")
        
        if missing:
            return {
                "complete": False,
                "missing_descriptions": missing,
                "message": f"以下字段缺少描述，建议先完善：{', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}"
            }
        
        return {
            "complete": True,
            "missing_descriptions": [],
            "message": "Schema 配置完整"
        }
    
    def get_schema(self, auto_generate: bool = True) -> Dict[str, Any]:
        """
        获取 Schema（优先级：SDK内存 > 本地文件 > 自动生成）
        
        Args:
            auto_generate: 如果内存和文件都没有，是否自动从数据库生成
        
        Returns:
            dict: Schema 信息
        """
        import json
        
        # 1. 优先从内存获取
        if self._cached_schema and self._cached_schema.get("entities"):
            return self._cached_schema
        
        # 2. 从本地文件获取
        if self._schema_file and self._schema_file.exists():
            try:
                with open(self._schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                    if schema and schema.get("entities"):
                        # 加载到内存
                        self.register_schema(
                            entities=schema["entities"],
                            system_name=schema.get("system_name"),
                            system_description=schema.get("system_description")
                        )
                        print("[SDK] Schema 从本地文件加载")
                        return self._cached_schema
            except Exception as e:
                print(f"[SDK] 读取 Schema 文件失败: {e}")
        
        # 3. 自动从数据库生成
        if auto_generate and self._db:
            try:
                result = self.generate_schema_from_db(use_ai=False)
                if result.get("success"):
                    # 保存到文件
                    if self._schema_file:
                        self.save_schema_to_file()
                    print("[SDK] Schema 从数据库自动生成")
                    return self._cached_schema
            except Exception as e:
                print(f"[SDK] 自动生成 Schema 失败: {e}")
        
        return self._cached_schema
    
    def generate_schema_from_db(self, use_ai: bool = False) -> Dict[str, Any]:
        """
        从数据库自动生成 Schema
        
        根据数据库表结构自动生成 Schema 配置
        
        Args:
            use_ai: 是否使用 AI 智能分析（更准确但较慢）
        
        Returns:
            dict: {
                "success": bool,
                "entities": list,  # 生成的实体列表
                "relations": list  # 表关联关系（AI 模式）
            }
        
        Example:
            >>> result = client.generate_schema_from_db(use_ai=True)
            >>> client.register_schema(entities=result["entities"])
        """
        if not self._db:
            raise AIAgentError("未配置数据库，请在初始化时传入 db_config")
        
        # 获取数据库表结构
        tables_info = self._get_tables_info(use_ai)
        
        if use_ai:
            # 调用 AI 分析
            result = self._request("POST", "/api/v1/schema/analyze", {
                "tables_info": tables_info
            })
            return {
                "success": True,
                "entities": result.get("entities", []),
                "relations": result.get("relations", [])
            }
        else:
            # 规则推断
            entities = self._infer_schema(tables_info)
            return {"success": True, "entities": entities}
    
    def _get_tables_info(self, include_sample: bool = False) -> List[Dict]:
        """获取数据库表结构信息"""
        from decimal import Decimal
        
        tables_info = []
        
        # 获取所有表
        tables = self._db.execute("SHOW TABLES")
        if not tables:
            return []
        
        # 获取数据库名
        db_result = self._db.execute("SELECT DATABASE()")
        database = db_result[0].get("DATABASE()") if db_result else ""
        
        for table_row in tables:
            table_name = list(table_row.values())[0]
            
            # 获取表注释
            table_info = self._db.execute(f"""
                SELECT TABLE_COMMENT FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table_name}'
            """)
            table_comment = table_info[0].get("TABLE_COMMENT", "") if table_info else ""
            
            # 获取字段信息
            columns_info = self._db.execute(f"""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = []
            for col in columns_info:
                col_type = col.get("COLUMN_TYPE", "").lower()
                field_type = "string"
                if "int" in col_type:
                    field_type = "integer"
                elif "decimal" in col_type or "float" in col_type or "double" in col_type:
                    field_type = "decimal"
                elif "datetime" in col_type or "timestamp" in col_type:
                    field_type = "datetime"
                elif "date" in col_type:
                    field_type = "date"
                elif "text" in col_type:
                    field_type = "text"
                elif "bool" in col_type or "tinyint(1)" in col_type:
                    field_type = "boolean"
                
                columns.append({
                    "name": col.get("COLUMN_NAME"),
                    "type": field_type,
                    "comment": col.get("COLUMN_COMMENT", ""),
                    "required": col.get("IS_NULLABLE") == "NO"
                })
            
            # 获取采样数据（用于 AI 分析）
            sample_data = []
            if include_sample:
                try:
                    rows = self._db.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                    for row in rows:
                        converted_row = {}
                        for k, v in row.items():
                            if hasattr(v, 'isoformat'):
                                converted_row[k] = v.isoformat()
                            elif isinstance(v, (bytes, bytearray)):
                                converted_row[k] = v.decode('utf-8', errors='ignore')
                            elif isinstance(v, Decimal):
                                converted_row[k] = float(v)
                            else:
                                converted_row[k] = v
                        sample_data.append(converted_row)
                except:
                    pass
            
            tables_info.append({
                "name": table_name,
                "table_comment": table_comment,
                "columns": columns,
                "sample_data": sample_data
            })
        
        return tables_info
    
    def _infer_schema(self, tables_info: List[Dict]) -> List[Dict]:
        """使用规则推断 Schema"""
        entities = []
        
        # 表名中文映射
        table_cn_map = {
            "student": "学生", "students": "学生",
            "class": "班级", "classes": "班级",
            "course": "课程", "courses": "课程",
            "score": "成绩", "scores": "成绩",
            "user": "用户", "users": "用户",
            "order": "订单", "orders": "订单",
            "product": "商品", "products": "商品",
            "teacher": "教师", "teachers": "教师",
            "class_courses": "班级课程关联",
        }
        
        # 字段名中文映射
        field_cn_map = {
            "id": "ID", "name": "名称", "title": "标题",
            "age": "年龄", "gender": "性别", "phone": "电话",
            "email": "邮箱", "address": "地址", "status": "状态",
            "created_at": "创建时间", "updated_at": "更新时间",
            "price": "价格", "amount": "数量", "total": "总计",
            "description": "描述", "remark": "备注",
        }
        
        for table in tables_info:
            fields = []
            for col in table["columns"]:
                # 优先使用数据库注释
                if col.get("comment") and col["comment"].strip():
                    description = col["comment"].strip()
                else:
                    # 使用映射或字段名
                    description = field_cn_map.get(col["name"].lower(), col["name"])
                
                fields.append({
                    "name": col["name"],
                    "type": col["type"],
                    "description": description,
                    "required": col.get("required", False)
                })
            
            # 表中文名
            table_comment = table.get("table_comment", "")
            if table_comment and table_comment.strip():
                chinese_name = table_comment.strip()
                table_desc = table_comment.strip()
            else:
                chinese_name = table_cn_map.get(table["name"].lower(), table["name"])
                table_desc = f"{table['name']} 表"
            
            entities.append({
                "name": table["name"],
                "chinese_name": chinese_name,
                "description": table_desc,
                "fields": fields
            })
        
        return entities
    
    def _check_schema(self):
        """检查是否已注册 Schema"""
        if not self._schema_registered:
            raise AIAgentError("请先调用 register_schema() 注册后台 Schema")
    
    # ============ 自然语言对话 ============
    
    def chat(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        与 AI Agent 对话
        
        发送自然语言指令，AI 会理解并返回建议的操作
        
        Args:
            message: 自然语言指令，如 "查询所有订单"
            conversation_id: 对话 ID（多轮对话时使用）
        
        Returns:
            dict: 包含 conversation_id, message, actions
            
        Example:
            >>> result = client.chat("查询所有订单")
            >>> print(result['message'])
            '我理解您想查询数据。以下是建议的操作：'
            >>> print(result['actions'])
            [{'id': 'action_xxx', 'type': 'list', 'entity': 'order', ...}]
        """
        self._check_schema()
        
        if not message or not message.strip():
            raise ValueError("message 不能为空")
        
        data = {"message": message.strip()}
        if conversation_id:
            data["conversation_id"] = conversation_id
        elif self._conversation_id:
            data["conversation_id"] = self._conversation_id
        
        result = self._request("POST", "/api/v1/chat", data)
        
        # 保存对话 ID 用于多轮对话
        self._conversation_id = result.get("conversation_id")
        
        return result
    
    def ask(self, question: str) -> str:
        """
        简化版对话，直接返回 AI 回复文本
        
        Args:
            question: 问题
        
        Returns:
            str: AI 回复
            
        Example:
            >>> answer = client.ask("查询所有订单")
            >>> print(answer)
        """
        result = self.chat(question)
        return result.get("message", "")
    
    # ============ 执行操作 ============
    
    def execute(
        self, 
        action_id: str, 
        conversation_id: str = None,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        执行 AI 建议的操作
        
        Args:
            action_id: 操作 ID（从 chat 返回的 actions 中获取）
            conversation_id: 对话 ID
            confirmed: 是否已确认（增删改操作需要设为 True）
        
        Returns:
            dict: 执行结果
            
        Example:
            >>> # 查询操作，直接执行
            >>> result = client.execute(action_id)
            
            >>> # 增删改操作，需要确认
            >>> result = client.execute(action_id, confirmed=True)
        """
        conv_id = conversation_id or self._conversation_id
        if not conv_id:
            raise AIAgentError("请先调用 chat() 获取操作建议")
        
        return self._request("POST", "/api/v1/execute", {
            "conversation_id": conv_id,
            "action_id": action_id,
            "confirmed": confirmed
        })
    
    def get_conversation(self, conversation_id: str = None) -> Dict[str, Any]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话 ID
        
        Returns:
            dict: 对话历史
        """
        conv_id = conversation_id or self._conversation_id
        if not conv_id:
            raise AIAgentError("没有活跃的对话")
        
        return self._request("GET", f"/api/v1/conversations/{conv_id}")
    
    # ============ 便捷方法 ============
    
    def new_conversation(self):
        """开始新对话"""
        self._conversation_id = None
        self._history = []
    
    # ============ 一键执行（核心方法） ============
    
    def ask_and_execute(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        一键完成：AI 理解 → 数据库执行 → 结果总结
        
        客户只需调用此方法，即可完成所有操作
        
        Args:
            message: 自然语言指令，如 "查询王五的成绩"
            history: 对话历史（可选），格式 [{"role": "user", "content": "..."}, ...]
        
        Returns:
            dict: {
                "success": bool,
                "message": str,      # AI 总结的回复
                "data": list/dict,   # 查询结果（如有）
                "steps": list        # 执行的步骤
            }
        
        Example:
            >>> result = client.ask_and_execute("查询王五的成绩")
            >>> print(result["message"])
            '王五同学的成绩如下：语文 95 分，数学 98 分'
        """
        self._check_schema()
        
        if not self._db:
            raise AIAgentError("未配置数据库，请在初始化时传入 db_config 或 db_adapter")
        
        # 合并历史
        combined_history = (history or []) + self._history[-20:]
        
        # 1. 调用 AI 处理（意图理解 + 规划）
        process_result = self._request("POST", "/api/v1/process", {
            "message": message,
            "conversation_id": self._conversation_id,
            "history": combined_history[-20:],  # 最近20条历史
            "schema": self._cached_schema  # 附带 Schema
        })
        
        self._conversation_id = process_result.get("conversation_id")
        steps = process_result.get("steps", [])
        intent = process_result.get("understood_message", message)
        
        # 保存历史
        self._history.append({"role": "user", "content": message})
        
        if not steps:
            # 普通对话，无需执行
            response = process_result.get("response", "你好！有什么可以帮你的吗？")
            self._history.append({"role": "assistant", "content": response})
            return {"success": True, "message": response, "data": None, "steps": []}
        
        # 2. 执行数据库操作
        step_results = {}
        for idx, step in enumerate(steps, 1):
            resolved_step = self._resolve_step_references(step, step_results)
            result = self._execute_query(resolved_step)
            step_results[idx] = result
        
        # 3. 调用 AI 总结结果
        serialized_results = self._serialize(step_results)
        summary_result = self._request("POST", "/api/v1/summarize", {
            "question": intent,
            "results": serialized_results,
            "conversation_id": self._conversation_id
        })
        
        summary = summary_result.get("message", "操作完成")
        self._history.append({"role": "assistant", "content": summary})
        
        # 获取最后一步的数据
        last_result = step_results.get(len(steps), {})
        
        return {
            "success": True,
            "message": summary,
            "data": last_result.get("data"),
            "steps": steps,
            "step_results": step_results,
            "intent": intent if intent != message else None
        }
    
    def chat_and_execute(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """ask_and_execute 的别名，保持兼容性"""
        return self.ask_and_execute(message, history)
    
    def parse_intent(self, message: str, history: List[Dict] = None, mode: str = "manage") -> Dict[str, Any]:
        """
        解析用户意图，返回操作步骤（不执行）
        
        Args:
            message: 用户消息
            history: 对话历史
            mode: 助手模式 (manage=通用助手, education=教务助手)
        
        Returns:
            dict: {"intent": str, "steps": list}
        """
        self._check_schema()
        
        combined_history = (history or []) + self._history[-20:]
        
        process_result = self._request("POST", "/api/v1/process", {
            "message": message,
            "conversation_id": self._conversation_id,
            "history": combined_history[-20:],
            "schema": self._cached_schema,
            "mode": mode
        })
        
        self._conversation_id = process_result.get("conversation_id")
        
        return {
            "intent": process_result.get("understood_message", message),
            "steps": process_result.get("steps", []),
            "response": process_result.get("response", ""),
            "names_to_confirm": process_result.get("names_to_confirm", [])
        }
    
    def process_chat_stream(self, message: str, history: List[Dict] = None, mode: str = "manage"):
        """
        流式处理对话请求，生成 SSE 事件
        
        Args:
            message: 用户消息
            history: 对话历史
            mode: 助手模式 (manage=通用助手, education=教务助手)
        
        Yields:
            str: SSE 格式的事件字符串
        
        Example:
            for event in client.process_chat_stream("查询学生"):
                yield event  # 直接用于 StreamingResponse
        """
        import json
        
        def send(type: str, **data):
            return f"data: {json.dumps({'type': type, **data}, ensure_ascii=False)}\n\n"
        
        def serialize(obj):
            from decimal import Decimal
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            elif hasattr(obj, 'strftime'):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        try:
            yield send("thinking", icon="🤖", text="正在分析...")
            
            # 检查 Schema 完整性
            schema_check = self.check_schema_completeness()
            if not schema_check.get("complete"):
                yield send("thinking", icon="⚠️", text=schema_check.get("message"))
                yield send("done", message=schema_check.get("message"), schema_incomplete=True)
                return
            
            # ========== 第1步：AI识别用户意图 + 列出执行步骤 ==========
            print(f"\n{'='*60}")
            print(f"[流程] 第1步：AI识别用户意图")
            print(f"[流程] 用户消息: {message}")
            print(f"[流程] 历史记录: {len(history) if history else 0}条")
            
            parse_result = self.parse_intent(message, history, mode)
            intent = parse_result.get("intent", "")
            steps = parse_result.get("steps", [])
            response = parse_result.get("response", "")
            
            # ========== 检查是否有名称需要确认（names_to_confirm） ==========
            names_to_confirm = parse_result.get("names_to_confirm", [])
            print(f"[流程] parse_result完整内容: {parse_result}")
            print(f"[流程] names_to_confirm: {names_to_confirm}")
            
            if names_to_confirm:
                print(f"[流程] 检测到{len(names_to_confirm)}个名称需要确认")
                yield send("thinking", icon="🔍", text="正在确认名称...")
                
                # 第二步：去数据库查询这些名称的相关结果
                lookup_results = []
                for item in names_to_confirm:
                    table = item.get("table", "")
                    keywords = item.get("keywords", [])  # AI已拆分好的关键词数组
                    # 兼容旧格式
                    if not keywords and item.get("keyword"):
                        keywords = [item.get("keyword")]
                    
                    if table and keywords:
                        # 使用AI拆分好的关键词构建模糊查询
                        like_parts = [f"name LIKE '%{kw}%'" for kw in keywords]
                        
                        # 先尝试AND条件
                        sql = f"SELECT id, name FROM {table} WHERE {' AND '.join(like_parts)} LIMIT 500"
                        print(f"[流程] 查询SQL(AND): {sql}")
                        
                        try:
                            records = self._db.execute_sql(sql)
                            
                            # 如果AND条件没结果，尝试OR条件
                            if not records and len(keywords) > 1:
                                sql = f"SELECT id, name FROM {table} WHERE {' OR '.join(like_parts)} LIMIT 500"
                                print(f"[流程] 查询SQL(OR): {sql}")
                                records = self._db.execute_sql(sql)
                            
                            # 如果还是没结果，查询该表所有数据供本地匹配
                            if not records:
                                sql = f"SELECT id, name FROM {table} LIMIT 100"
                                print(f"[流程] 查询全部: {sql}")
                                records = self._db.execute_sql(sql)
                            
                            lookup_results.append({
                                "table": table,
                                "keywords": keywords,
                                "data": records
                            })
                            print(f"[流程] 查询 {table}({keywords}): {len(records)}条记录")
                        except Exception as e:
                            print(f"[流程] 查询失败: {e}")
                            lookup_results.append({
                                "table": table,
                                "keywords": keywords,
                                "data": [],
                                "error": str(e)
                            })
                
                # 第三步：使用本地相似度匹配确认名称（比AI快）
                print(f"[流程] 使用本地相似度匹配确认名称")
                confirmed_names = self._confirm_names_local(lookup_results)
                print(f"[流程] 确认结果: {confirmed_names}")
                
                # 构建确认结果上下文（格式必须与提示词中的"情况2"匹配）
                confirm_context = "\n\n## 名称确认结果\n"
                has_valid_filter = False
                for result in confirmed_names:
                    table_name = {"semester": "学期", "class": "班级", "student": "学生", "course": "课程"}.get(result["table"], result["table"])
                    if result.get("skip_filter"):
                        # 相似度太低，告诉AI不要添加这个筛选条件
                        options = result.get("available_options", [])
                        if options:
                            confirm_context += f"- {table_name}({result['table']}表): 找不到匹配，忽略此条件\n"
                        else:
                            confirm_context += f"- {table_name}({result['table']}表): 找不到匹配，忽略此条件\n"
                    else:
                        confirm_context += f"- {table_name}({result['table']}表): ID={result.get('id')}, 名称=\"{result.get('name')}\"\n"
                        has_valid_filter = True
                
                confirm_context += "\n请使用以上ID生成SQL步骤。\n"
                
                # 第四步：生成最终SQL
                print(f"[流程] 生成最终SQL")
                print(f"[流程] 确认上下文: {confirm_context}")
                confirm_message = f"{message}{confirm_context}"
                parse_result = self.parse_intent(confirm_message, history, mode)
                intent = parse_result.get("intent", intent)
                steps = parse_result.get("steps", [])
                response = parse_result.get("response", "")
                print(f"[流程] 最终步骤: {steps}")
            
            print(f"[流程] AI返回:")
            print(f"  - 意图: {intent}")
            print(f"  - 步骤: {steps}")
            print(f"  - 回复: {response[:100] if response else 'None'}...")
            
            # ========== 第2步：判断是否有步骤 ==========
            print(f"\n[流程] 第2步：判断是否有执行步骤")
            if not steps:
                print(f"[流程] 无步骤，直接返回AI回复")
                yield send("thinking", icon="💬", text="AI直接回复")
                yield send("done", message=response or "你好！有什么可以帮你的？", intent=message)
                return
            
            print(f"[流程] 有{len(steps)}个步骤需要执行")
            if intent:
                yield send("thinking", icon="🧠", text=f'理解意图: "{message}" → "{intent}"')
            
            # 检查是否有危险操作
            dangerous_actions = ["delete", "update", "create"]
            has_dangerous = any(step.get("action") in dangerous_actions for step in steps)
            
            if has_dangerous and steps:
                # 生成预览信息
                action_map = {"query": "查询", "create": "创建", "update": "更新", "delete": "删除", "aggregate": "统计"}
                preview = "即将执行以下操作：\n"
                for idx, step in enumerate(steps, 1):
                    action_name = action_map.get(step.get("action"), step.get("action"))
                    preview += f"\n{idx}. **{action_name}** `{step.get('entity', '')}`"
                    if step.get("where"):
                        preview += f"\n   条件: {json.dumps(step['where'], ensure_ascii=False)}"
                    if step.get("data"):
                        preview += f"\n   数据: {json.dumps(step['data'], ensure_ascii=False)}"
                
                yield send("thinking", icon="⚠️", text="检测到数据修改操作，需要确认")
                yield send("confirm", message=preview, intent=intent, steps=steps, original_message=message)
                return
            
            # ========== 第3步：执行数据库操作 ==========
            print(f"\n[流程] 第3步：执行数据库操作")
            if steps:
                yield send("thinking", icon="⚡", text=f"执行 {len(steps)} 个操作步骤...")
                result = self.execute_steps(steps, message, intent, mode)  # 传递intent和mode用于总结
                step_results = result.get("step_results", {})
                
                # 检查是否需要用户确认
                if result.get("need_confirm"):
                    print(f"[流程] 需要用户确认: {result.get('sql')}")
                    yield send("done", 
                        need_confirm=True,
                        sql=result.get("sql"),
                        sql_type=result.get("sql_type"),
                        confirm_token=result.get("confirm_token", ""),
                        before_data=result.get("before_data", ""),
                        message=result.get("message", "此操作需要您确认后才能执行")
                    )
                    return
                
                # 检查是否有Excel文件或下载token
                excel_path = None
                download_token = None
                for idx, sr in step_results.items():
                    if sr.get("download_token"):
                        download_token = sr.get("download_token")
                        break
                    if sr.get("excel_path"):
                        excel_path = sr.get("excel_path")
                        break
                
                print(f"[流程] 执行结果: success={result.get('success')}, download_token={download_token}, excel_path={excel_path}")
                
                # ========== 第4步：AI总结结果 ==========
                print(f"\n[流程] 第4步：AI总结结果")
                yield send("thinking", icon="✅", text="完成")
                
                message_text = result.get("message", "")
                
                serialized_step_results = serialize(step_results)
                print(f"[SDK] step_results keys: {list(step_results.keys())}")
                print(f"[SDK] serialized_step_results: {list(serialized_step_results.keys()) if isinstance(serialized_step_results, dict) else 'not dict'}")
                
                done_data = {
                    "message": message_text,
                    "intent": intent,
                    "steps": steps,
                    "step_results": serialized_step_results
                }
                if download_token:
                    done_data["download_token"] = download_token
                    done_data["has_excel"] = True
                elif excel_path:
                    done_data["excel_path"] = excel_path
                    done_data["has_excel"] = True
                
                yield send("done", **done_data)
            else:
                # 无操作步骤，返回response或默认回复
                yield send("thinking", icon="💬", text="对话回复")
                yield send("done", message=response or "你好！有什么可以帮你的吗？", intent=message)
            
        except Exception as e:
            yield send("error", message=f"处理失败: {str(e)}")
    
    def process_chat(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        处理对话请求（用于流式接口）
        
        返回处理结果，包含是否需要确认、操作步骤等信息
        
        Args:
            message: 用户消息
            history: 对话历史
        
        Returns:
            dict: {
                "need_confirm": bool,  # 是否需要确认（危险操作）
                "intent": str,         # 理解后的意图
                "steps": list,         # 操作步骤
                "preview": str,        # 操作预览（需确认时）
                "result": dict,        # 执行结果（不需确认时）
                "schema_error": str    # Schema 错误信息（如有）
            }
        """
        # 检查 Schema 完整性
        schema_check = self.check_schema_completeness()
        if not schema_check.get("complete"):
            return {"schema_error": schema_check.get("message")}
        
        # 解析意图
        parse_result = self.parse_intent(message, history)
        intent = parse_result.get("intent")
        steps = parse_result.get("steps", [])
        
        # 检查是否有危险操作
        dangerous_actions = ["delete", "update", "create"]
        has_dangerous = any(step.get("action") in dangerous_actions for step in steps)
        
        if has_dangerous and steps:
            # 生成预览信息
            action_map = {"query": "查询", "create": "创建", "update": "更新", "delete": "删除", "aggregate": "统计"}
            preview = "即将执行以下操作：\n"
            for idx, step in enumerate(steps, 1):
                action_name = action_map.get(step.get("action"), step.get("action"))
                preview += f"\n{idx}. **{action_name}** `{step.get('entity', '')}`"
                if step.get("where"):
                    import json
                    preview += f"\n   条件: {json.dumps(step['where'], ensure_ascii=False)}"
                if step.get("data"):
                    import json
                    preview += f"\n   数据: {json.dumps(step['data'], ensure_ascii=False)}"
            
            return {
                "need_confirm": True,
                "intent": intent,
                "steps": steps,
                "preview": preview,
                "original_message": message
            }
        
        # 直接执行查询操作
        result = self.execute_steps(steps, message)
        return {
            "need_confirm": False,
            "intent": intent,
            "steps": steps,
            "result": result
        }
    
    def execute_steps(self, steps: List[Dict], original_message: str = "", intent: str = None, mode: str = "manage") -> Dict[str, Any]:
        """
        执行操作步骤
        
        Args:
            steps: 操作步骤列表
            original_message: 原始用户消息（用于总结）
            intent: AI理解的用户意图（用于更准确的总结）
            mode: 助手模式 (manage=通用助手, education=教务助手)
        
        Returns:
            dict: {"success": bool, "message": str, "step_results": dict}
        """
        if not self._db:
            raise AIAgentError("未配置数据库")
        
        if not steps:
            return {"success": True, "message": "无需执行操作", "step_results": {}}
        
        # 执行数据库操作
        print(f"\n[SDK] ========== execute_steps ==========")
        print(f"[SDK] 共{len(steps)}个步骤")
        step_results = {}
        for idx, step in enumerate(steps, 1):
            print(f"[SDK] 步骤{idx}: {step}")
            
            # 检查是否是SQL模式
            if "sql" in step:
                sql = step.get("sql")
                sql_type = step.get("type", "query")  # 默认为query
                
                # 解析SQL中的变量引用（如 $1.id, $2.name）
                sql = self._resolve_sql_references(sql, step_results)
                
                result = self._execute_sql(sql, sql_type)
            else:
                # 兼容旧的action/entity模式
                resolved_step = self._resolve_step_references(step, step_results)
                print(f"[SDK] 解析后: {resolved_step}")
                result = self._execute_query(resolved_step)
            
            step_results[idx] = result
            
            # 如果需要用户确认，返回确认请求
            if result.get("need_confirm"):
                return {
                    "success": True,
                    "need_confirm": True,
                    "sql": result.get("sql"),
                    "sql_type": result.get("sql_type"),
                    "confirm_token": result.get("confirm_token", ""),
                    "before_data": result.get("before_data", ""),
                    "message": result.get("message"),
                    "step_results": step_results
                }
            
            # 如果操作失败，直接返回错误
            if not result.get("success"):
                return {
                    "success": False,
                    "message": result.get("error", "操作失败"),
                    "step_results": step_results
                }
        
        # 调用 AI 总结结果
        serialized_results = self._serialize(step_results)
        summary_result = self._request("POST", "/api/v1/summarize", {
            "question": original_message,
            "results": serialized_results,
            "conversation_id": self._conversation_id,
            "schema": self._cached_schema,  # 传递schema以获取system_name
            "intent": intent,  # 传递AI理解的意图
            "mode": mode  # 传递助手模式
        })
        
        summary = summary_result.get("message", "操作完成")
        self._history.append({"role": "user", "content": original_message})
        self._history.append({"role": "assistant", "content": summary})
        
        return {
            "success": True,
            "message": summary,
            "step_results": step_results
        }
    
    def _execute_sql(self, sql: str, sql_type: str = "query") -> dict:
        """执行原生SQL语句（带安全检查）"""
        print(f"[SDK] 执行SQL: {sql}, type={sql_type}")
        
        # SQL安全检查
        sql_upper = sql.upper().strip()
        
        # 禁止危险操作（使用更精确的匹配，避免误判字段名如createdAt）
        dangerous_patterns = [
            "DROP TABLE", "DROP DATABASE", "DROP INDEX",
            "TRUNCATE TABLE", "TRUNCATE ",
            "ALTER TABLE", "ALTER DATABASE",
            "CREATE TABLE", "CREATE DATABASE", "CREATE INDEX",
            "GRANT ", "REVOKE ",
            "EXEC ", "EXECUTE ",
            "XP_", "SP_"
        ]
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                return {"success": False, "error": f"禁止执行危险操作: {pattern.strip()}"}
        
        # 禁止多语句执行（防止SQL注入）
        if ";" in sql and sql.count(";") > 1:
            return {"success": False, "error": "禁止执行多条SQL语句"}
        
        # 禁止注释（可能用于绕过检查）
        if "--" in sql or "/*" in sql:
            return {"success": False, "error": "SQL中不允许包含注释"}
        
        # 限制DELETE和UPDATE必须有WHERE条件
        if sql_upper.startswith("DELETE") or sql_upper.startswith("UPDATE"):
            if "WHERE" not in sql_upper:
                return {"success": False, "error": "DELETE/UPDATE操作必须包含WHERE条件"}
        
        # 双重验证：检查SQL语句实际类型
        # 去除前导空格和换行后检查
        sql_trimmed = sql_upper.strip()
        is_actually_select = sql_trimmed.startswith("SELECT") or sql_trimmed.startswith("WITH")
        is_actually_modify = sql_trimmed.startswith(("INSERT", "UPDATE", "DELETE"))
        
        # 额外检查：即使是SELECT开头，也检查是否包含修改关键字（防止注入）
        modify_keywords_in_sql = any(kw in sql_upper for kw in ["INSERT INTO", "UPDATE ", "DELETE FROM"])
        
        # 如果AI标记为query但实际是修改操作，需要用户确认
        if sql_type == "query" and (is_actually_modify or modify_keywords_in_sql):
            print(f"[SDK] 双重验证：AI标记为query但检测到修改操作，需要用户确认")
            before_data = self._get_affected_data_preview(sql)
            token = self._store_pending_sql(sql, "modify")
            return {
                "success": True,
                "need_confirm": True,
                "sql_type": "modify",
                "sql": sql,  # 仅用于显示
                "confirm_token": token,  # 用于确认执行
                "before_data": before_data,
                "message": "检测到这是一个修改操作，需要您确认后才能执行"
            }
        
        # 非查询操作需要用户确认（使用AI返回的type）
        if sql_type == "modify":
            before_data = self._get_affected_data_preview(sql)
            token = self._store_pending_sql(sql, sql_type)
            return {
                "success": True,
                "need_confirm": True,
                "sql_type": sql_type,
                "sql": sql,  # 仅用于显示
                "confirm_token": token,  # 用于确认执行
                "before_data": before_data,
                "message": "此操作需要您确认后才能执行"
            }
        
        try:
            records = self._db.execute_sql(sql)
            total_count = len(records)
            print(f"[SDK] SQL返回: {total_count}条记录")
            
            # 透视成绩数据（如果是成绩数据），确保前端和Excel格式一致
            pivoted_records = self._pivot_score_data(records)
            pivoted_count = len(pivoted_records)
            
            # 如果数据超过20条，生成下载token（延迟生成Excel）
            if pivoted_count > 20:
                download_token = self._store_export_data(records)  # 存储原始数据，下载时再pivot
                return {
                    "success": True,
                    "data": pivoted_records[:20],  # 前端表格只显示20条（已pivot）
                    "full_data": pivoted_records,  # AI分析使用全部数据（已pivot）
                    "total": pivoted_count,
                    "download_token": download_token,
                    "message": f"数据量较大（共{pivoted_count}条），点击下载完整数据"
                }
            
            return {"success": True, "data": pivoted_records, "full_data": pivoted_records, "total": pivoted_count}
        except Exception as e:
            print(f"[SDK] SQL执行错误: {e}")
            error_msg = str(e)
            # 检查是否是字段不存在的错误，提示用户更新schema
            if "Unknown column" in error_msg or "no such column" in error_msg.lower():
                error_msg += "\n\n提示：数据库结构可能已更新，请检查schema配置是否与数据库一致。"
            return {"success": False, "error": error_msg}
    
    def _normalize_name(self, name: str) -> str:
        """
        标准化名称，统一中文数字和阿拉伯数字，忽略大小写
        
        用于名称匹配时的预处理，确保用户输入的各种变体都能匹配到正确记录
        """
        # 中文数字到阿拉伯数字的映射
        cn_to_num = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', 
                     '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
                     '零': '0', '〇': '0'}
        result = name
        for cn, num in cn_to_num.items():
            result = result.replace(cn, num)
        
        # 始终忽略大小写（用户输入时通常不注意大小写）
        return result.lower().strip()
    
    def _find_similar_name_local(self, input_name: str, candidates: list) -> tuple:
        """
        本地相似度匹配，找到最相似的名称
        
        Args:
            input_name: 用户输入的名称
            candidates: 候选记录列表 [{"id": 1, "name": "xxx"}, ...]
        
        Returns:
            (最佳匹配记录, 匹配度) 或 (None, 0)
        """
        from difflib import SequenceMatcher
        
        if not candidates:
            return None, 0
        
        best_match = None
        best_ratio = 0
        
        # 标准化输入名称
        normalized_input = self._normalize_name(input_name)
        
        for record in candidates:
            name = record.get("name", "")
            if not name:
                continue
            
            # 标准化候选名称
            normalized_name = self._normalize_name(name)
            
            # 计算相似度
            ratio = SequenceMatcher(None, normalized_input, normalized_name).ratio()
            
            # 如果完全包含，提高匹配度
            if normalized_input in normalized_name or normalized_name in normalized_input:
                ratio = max(ratio, 0.85)
            
            # 如果标准化后完全相等
            if normalized_input == normalized_name:
                ratio = 1.0
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = record
        
        return best_match, best_ratio
    
    def _confirm_names_local(self, lookup_results: list) -> list:
        """
        使用本地相似度匹配确认名称（比AI快）
        
        当相似度低于阈值时，返回None表示需要查全部数据
        
        Args:
            lookup_results: 数据库查询结果 [{"table": "semester", "keywords": [...], "data": [...]}]
        
        Returns:
            确认后的名称列表 [{"table": "semester", "id": 1, "name": "2024年秋季学期", "skip_filter": True/False}]
            skip_filter=True 表示相似度太低，应该忽略这个条件查全部数据
        """
        confirmed = []
        
        for result in lookup_results:
            table = result.get("table", "")
            keywords = result.get("keywords", [])
            data = result.get("data", [])
            
            # 合并关键词作为输入
            input_name = " ".join(keywords) if keywords else ""
            
            if not data:
                # 没有候选数据，跳过这个筛选条件
                confirmed.append({
                    "table": table,
                    "id": None,
                    "name": input_name,
                    "skip_filter": True  # 找不到数据，跳过这个条件
                })
                print(f"[SDK] 本地匹配: '{input_name}' 无候选数据，跳过此筛选条件")
                continue
            
            # 本地相似度匹配
            best_match, ratio = self._find_similar_name_local(input_name, data)
            
            if best_match and ratio >= 0.85:
                # 匹配度>=0.85，高度确信，直接使用
                confirmed.append({
                    "table": table,
                    "id": best_match.get("id"),
                    "name": best_match.get("name"),
                    "skip_filter": False
                })
                print(f"[SDK] 本地匹配(高确信): '{input_name}' -> '{best_match.get('name')}' (相似度: {ratio:.2f})")
            elif best_match and ratio >= 0.7:
                # 匹配度0.7-0.85，中等确信，使用但提示可能不准确
                confirmed.append({
                    "table": table,
                    "id": best_match.get("id"),
                    "name": best_match.get("name"),
                    "skip_filter": False,
                    "uncertain": True  # 标记为不确定
                })
                print(f"[SDK] 本地匹配(中等确信): '{input_name}' -> '{best_match.get('name')}' (相似度: {ratio:.2f})")
            else:
                # 匹配度<0.7，跳过这个筛选条件，查全部数据
                confirmed.append({
                    "table": table,
                    "id": None,
                    "name": input_name,
                    "skip_filter": True,  # 相似度太低，跳过这个条件
                    "available_options": [d.get("name") for d in data[:5]]  # 提供可用选项
                })
                print(f"[SDK] 本地匹配: '{input_name}' 相似度太低({ratio:.2f})，跳过此筛选条件，查全部数据")
        
        return confirmed
    
    def _confirm_names_with_ai(self, names_to_confirm: list, lookup_results: list) -> list:
        """
        调用专门的确认名称AI Agent，确认用户说的是哪个具体记录
        （现在优先使用本地匹配，只有需要时才调用AI）
        
        Args:
            names_to_confirm: 需要确认的名称列表 [{"table": "semester", "keyword": "2024秋季"}]
            lookup_results: 数据库查询结果 [{"table": "semester", "keyword": "2024秋季", "data": [...]}]
        
        Returns:
            确认后的名称列表 [{"table": "semester", "id": 1, "name": "2024年秋季学期"}]
        """
        confirmed = []
        
        # 构建确认提示词
        prompt_parts = ["你是名称确认助手。根据用户说的关键词和数据库查询结果，确认用户指的是哪条记录。\n"]
        prompt_parts.append("**重要规则**：你只能从数据库查询结果中选择，不能自己编造ID或名称！\n")
        
        for i, result in enumerate(lookup_results):
            table = result.get("table", "")
            keywords = result.get("keywords", [])
            data = result.get("data", [])
            
            prompt_parts.append(f"\n## 第{i+1}个名称")
            prompt_parts.append(f"用户说的关键词: {keywords}")
            prompt_parts.append(f"表名: {table}")
            prompt_parts.append("数据库查询结果:")
            
            if data:
                for record in data[:5]:
                    prompt_parts.append(f"  - ID: {record.get('id')}, 名称: {record.get('name')}")
            else:
                prompt_parts.append("  无匹配记录")
        
        prompt_parts.append("\n**返回规则**：")
        prompt_parts.append(f"1. 必须返回{len(lookup_results)}个结果，每个名称都要有对应的确认结果")
        prompt_parts.append("2. 优先从数据库查询结果中选择最匹配的记录")
        prompt_parts.append("3. 如果查询结果为空或找不到匹配项，使用原始关键词作为name，id设为null")
        prompt_parts.append("4. 返回JSON数组，每个元素包含table、id、name")
        prompt_parts.append('例如: [{"table": "semester", "id": 4, "name": "2025春季"}]')
        prompt_parts.append("只返回JSON数组：")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            result = self._request("POST", "/api/v1/confirm_names", {
                "prompt": prompt,
                "conversation_id": self._conversation_id
            })
            confirmed = result.get("confirmed", [])
        except Exception as e:
            print(f"[SDK] 确认名称失败: {e}")
            # 如果AI调用失败，使用第一条记录作为默认值
            for result in lookup_results:
                data = result.get("data", [])
                if data:
                    confirmed.append({
                        "table": result.get("table"),
                        "id": data[0].get("id"),
                        "name": data[0].get("name")
                    })
                else:
                    confirmed.append({
                        "table": result.get("table"),
                        "id": None,
                        "name": result.get("keyword")
                    })
        
        return confirmed
    
    def _resolve_sql_references(self, sql: str, step_results: dict) -> str:
        """解析SQL中的变量引用（如 $1.id, $2.name, $1）"""
        import re
        
        def replace_field_ref(match):
            """替换 $1.fieldName 格式"""
            step_num = int(match.group(1))
            field_name = match.group(2)
            
            prev_result = step_results.get(step_num, {})
            data = prev_result.get("data", [])
            
            if data and len(data) > 0:
                value = data[0].get(field_name)
                if value is not None:
                    if isinstance(value, str):
                        return f"'{value}'"
                    return str(value)
            
            return match.group(0)
        
        def replace_simple_ref(match):
            """替换 $1 格式（取第一个字段的值）"""
            step_num = int(match.group(1))
            
            prev_result = step_results.get(step_num, {})
            data = prev_result.get("data", [])
            
            if data and len(data) > 0:
                # 取第一条记录的第一个字段值
                first_key = list(data[0].keys())[0]
                value = data[0].get(first_key)
                if value is not None:
                    if isinstance(value, str):
                        return f"'{value}'"
                    return str(value)
            
            return match.group(0)
        
        # 先匹配 $1.fieldName 格式
        resolved_sql = re.sub(r'\$(\d+)\.(\w+)', replace_field_ref, sql)
        # 再匹配 $1 格式（不带字段名）
        resolved_sql = re.sub(r'\$(\d+)(?!\.\w)', replace_simple_ref, resolved_sql)
        return resolved_sql
    
    def _export_to_excel_from_records(self, records: list) -> str:
        """从记录列表导出Excel"""
        import os
        import tempfile
        import csv
        from datetime import datetime
        
        if not records:
            return None
        
        # 透视成绩数据（如果是成绩数据）
        records = self._pivot_score_data(records)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"
        export_dir = self._export_dir or tempfile.gettempdir()
        filepath = os.path.join(export_dir, filename)
        
        # 使用记录中的字段名作为表头（已经是中文别名）
        headers = list(records[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for record in records:
                row = []
                for h in headers:
                    v = record.get(h, '')
                    if hasattr(v, 'strftime'):
                        row.append(v.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        row.append(v)
                writer.writerow(row)
        
        print(f"[SDK] 已导出Excel: {filepath}, 共{len(records)}条记录")
        return filepath
    
    def _pivot_score_data(self, records: list) -> list:
        """
        透视成绩数据：将长格式（每行一条成绩）转换为宽格式（按学生分组，科目作为列）
        """
        if not records or len(records) == 0:
            return records
        
        first_record = records[0]
        subject_field = None
        score_field = None
        
        # 检测科目字段
        for field in ['科目', '课程', '课程名称', 'subject', 'course', 'courseName', 'course_name']:
            if field in first_record:
                subject_field = field
                break
        
        # 检测成绩字段
        for field in ['成绩', '分数', 'score', '得分']:
            if field in first_record:
                score_field = field
                break
        
        if not subject_field or not score_field:
            return records
        
        # 确定分组字段
        group_fields = []
        for field in ['学生姓名', '姓名', '学生', 'studentName', 'student_name', 'name']:
            if field in first_record:
                group_fields.append(field)
                break
        
        for field in ['班级', '学期', 'class', 'semester', 'className', 'semesterName']:
            if field in first_record and field not in group_fields:
                group_fields.append(field)
        
        if not group_fields:
            return records
        
        print(f"[SDK] 透视成绩数据: 分组={group_fields}, 科目={subject_field}, 成绩={score_field}")
        
        # 收集所有科目
        subjects = []
        for record in records:
            subj = record.get(subject_field)
            if subj and subj not in subjects:
                subjects.append(subj)
        
        # 按分组字段聚合
        grouped = {}
        for record in records:
            key = '|'.join([str(record.get(f, '')) for f in group_fields])
            
            if key not in grouped:
                grouped[key] = {f: record.get(f) for f in group_fields}
                for subj in subjects:
                    grouped[key][subj] = ''
            
            subj = record.get(subject_field)
            score = record.get(score_field)
            if subj:
                grouped[key][subj] = score
        
        pivoted = list(grouped.values())
        print(f"[SDK] 透视完成: {len(records)}条 -> {len(pivoted)}条")
        return pivoted
    
    def _store_pending_sql(self, sql: str, sql_type: str) -> str:
        """存储待确认的SQL到Redis，返回token（5分钟过期）"""
        import uuid
        import json
        import time
        
        # 生成唯一token：UUID + 时间戳，确保不重复
        token = f"{uuid.uuid4().hex}_{int(time.time() * 1000)}"
        data = json.dumps({
            "sql": sql,
            "sql_type": sql_type
        })
        
        # 优先使用Redis
        if self._redis:
            try:
                key = f"pending_sql:{token}"
                # 检查key是否已存在（理论上不可能，但做双重保险）
                if self._redis.exists(key):
                    # 极端情况：重新生成
                    token = f"{uuid.uuid4().hex}_{int(time.time() * 1000)}_retry"
                    key = f"pending_sql:{token}"
                # 存储到Redis，5分钟过期
                self._redis.setex(key, 300, data)  # 300秒 = 5分钟
                print(f"[SDK] 存储待确认SQL到Redis，token: {token}")
                return token
            except Exception as e:
                print(f"[SDK] Redis存储失败: {e}")
        
        # 降级到内存存储
        import time
        current_time = time.time()
        # 清理过期的pending SQL（超过5分钟）
        expired_tokens = [t for t, v in self._pending_sql.items() if current_time - v.get("created_at", 0) > 300]
        for t in expired_tokens:
            del self._pending_sql[t]
        
        self._pending_sql[token] = {
            "sql": sql,
            "sql_type": sql_type,
            "created_at": current_time
        }
        print(f"[SDK] 存储待确认SQL到内存，token: {token}")
        return token
    
    def _get_affected_data_preview(self, sql: str) -> str:
        """获取将被修改的数据预览（用于确认弹框）"""
        import re
        sql_upper = sql.upper().strip()
        
        print(f"[SDK] 获取预览数据，SQL: {sql}")
        
        try:
            # 从UPDATE/DELETE语句中提取WHERE条件
            if sql_upper.startswith("UPDATE"):
                # UPDATE table SET ... WHERE ...
                # 更宽松的正则，支持各种格式
                match = re.search(r'UPDATE\s+(\w+)\s+SET\s+.*?(WHERE\s+.+)$', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    table = match.group(1)
                    where_clause = match.group(2)
                    preview_sql = f"SELECT * FROM {table} {where_clause} LIMIT 10"
                    print(f"[SDK] 预览SQL: {preview_sql}")
                    records = self._db.execute_sql(preview_sql)
                    print(f"[SDK] 预览数据: {len(records) if records else 0}条")
                    if records:
                        return self._format_preview_table(records)
                else:
                    print(f"[SDK] UPDATE正则匹配失败")
            elif sql_upper.startswith("DELETE"):
                # DELETE FROM table WHERE ...
                match = re.search(r'DELETE\s+FROM\s+(\w+)\s+(WHERE\s+.+)$', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    table = match.group(1)
                    where_clause = match.group(2)
                    preview_sql = f"SELECT * FROM {table} {where_clause} LIMIT 10"
                    print(f"[SDK] 预览SQL: {preview_sql}")
                    records = self._db.execute_sql(preview_sql)
                    print(f"[SDK] 预览数据: {len(records) if records else 0}条")
                    if records:
                        return self._format_preview_table(records)
                else:
                    print(f"[SDK] DELETE正则匹配失败")
        except Exception as e:
            print(f"[SDK] 获取预览数据失败: {e}")
            import traceback
            traceback.print_exc()
        
        return ""
    
    def _format_preview_table(self, records: list) -> str:
        """将记录格式化为Markdown表格"""
        if not records:
            return ""
        
        headers = list(records[0].keys())
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for record in records[:10]:
            row = []
            for h in headers:
                v = record.get(h, '')
                if hasattr(v, 'strftime'):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                row.append(str(v) if v is not None else '')
            lines.append("| " + " | ".join(row) + " |")
        
        if len(records) > 10:
            lines.append(f"\n*（仅显示前10条，共{len(records)}条将被影响）*")
        else:
            lines.append(f"\n*（共{len(records)}条将被影响）*")
        
        return "\n".join(lines)
    
    def cancel_pending_sql(self, token: str) -> dict:
        """取消待确认的SQL，删除Redis/内存中的key"""
        print(f"[SDK] 取消待确认SQL，token: {token}")
        
        deleted = False
        
        # 优先从Redis删除
        if self._redis:
            try:
                key = f"pending_sql:{token}"
                result = self._redis.delete(key)
                if result > 0:
                    deleted = True
                    print(f"[SDK] 已从Redis删除token: {token}")
            except Exception as e:
                print(f"[SDK] Redis删除失败: {e}")
        
        # 也从内存删除（以防万一）
        if token in self._pending_sql:
            del self._pending_sql[token]
            deleted = True
            print(f"[SDK] 已从内存删除token: {token}")
        
        return {"success": True, "deleted": deleted}
    
    def execute_confirmed_sql(self, token: str) -> dict:
        """通过token执行用户确认后的SQL（防止SQL注入）"""
        import json as json_lib
        print(f"[SDK] 执行已确认的SQL，token: {token}")
        
        if not self._db:
            return {"success": False, "error": "未配置数据库"}
        
        sql = None
        
        # 优先从Redis获取
        if self._redis:
            try:
                key = f"pending_sql:{token}"
                data = self._redis.get(key)
                if data:
                    pending = json_lib.loads(data)
                    sql = pending.get("sql")
                    # 删除已使用的token（一次性使用）
                    self._redis.delete(key)
                    print(f"[SDK] 从Redis获取SQL: {sql}")
            except Exception as e:
                print(f"[SDK] Redis获取失败: {e}")
        
        # 降级到内存获取
        if not sql:
            pending = self._pending_sql.get(token)
            if pending:
                sql = pending.get("sql")
                del self._pending_sql[token]
                print(f"[SDK] 从内存获取SQL: {sql}")
        
        if not sql:
            return {"success": False, "error": "确认token无效或已过期"}
        
        sql_upper = sql.upper().strip()
        
        try:
            # 执行SQL
            if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
                records = self._db.execute_sql(sql)
                return {"success": True, "data": records, "total": len(records), "message": f"查询成功，共{len(records)}条记录"}
            else:
                # INSERT/UPDATE/DELETE
                result = self._db.execute_sql(sql)
                affected = result if isinstance(result, int) else len(result) if isinstance(result, list) else 1
                return {"success": True, "affected_rows": affected, "message": f"操作成功，影响{affected}条记录"}
        except Exception as e:
            print(f"[SDK] SQL执行错误: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_query(self, query: dict) -> dict:
        """执行 AI 生成的查询指令"""
        import re
        
        action = query.get("action")
        entity = query.get("entity")
        where = query.get("where") or {}
        if not isinstance(where, dict):
            where = {}
        order_by = query.get("orderBy") or query.get("order_by")  # 兼容两种格式
        order = query.get("order", "asc")
        limit = query.get("limit", 1000)  # 默认不限制，返回所有记录
        
        # 如果limit是字符串，转换为整数
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except:
                limit = 1000
        data = query.get("data") or {}
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        if not isinstance(data, dict):
            data = {}
        
        if not entity:
            return {"success": False, "error": "缺少实体名"}
        
        try:
            # 处理子查询条件（支持嵌套子查询）
            print(f"\n[SDK] ========== 执行查询 ==========")
            print(f"[SDK] action={action}, entity={entity}")
            print(f"[SDK] where条件: {where}")
            
            resolved_where = self._resolve_subqueries(where)
            print(f"[SDK] 解析子查询后: {resolved_where}")
            
            print(f"[SDK] 解析后的where条件: {resolved_where}")
            
            # 查询数据 - 如果有过滤条件，需要查询全部数据
            # 否则可能会漏掉符合条件的记录
            query_limit = 100000 if resolved_where else 1000
            records, total = self._db.list(entity, {}, limit=query_limit)
            print(f"[SDK] 查询{entity}表: 返回{len(records)}条, 总共{total}条")
            
            # 条件过滤（在外键解析之前，使用原始字段名过滤）
            for key, value in resolved_where.items():
                if value is not None:
                    if isinstance(value, list):
                        records = [r for r in records if r.get(key) in value]
                    else:
                        records = [r for r in records if r.get(key) == value]
            
            print(f"[SDK] 过滤后: {len(records)}条")
            
            # 自动关联外键名称（从Schema动态读取）
            records = self._resolve_foreign_keys(entity, records)
            
            if action == "query":
                print(f"[SDK] orderBy={order_by}, order={order}, limit={limit}")
                if order_by:
                    reverse = order == "desc"
                    # 处理可能的None值
                    records = sorted(records, key=lambda x: x.get(order_by) or 0, reverse=reverse)
                
                total_count = len(records)
                records = records[:limit]
                print(f"[SDK] 排序后取前{limit}条，实际返回{len(records)}条")
                
                # 如果数据超过20条且实际返回超过20条，生成下载token
                if total_count > 20 and len(records) > 20:
                    download_token = self._store_export_data(records)
                    return {
                        "success": True, 
                        "action": action, 
                        "entity": entity, 
                        "data": records[:20],  # 前端表格只显示20条
                        "full_data": records,  # AI分析使用全部数据
                        "total": total_count,
                        "download_token": download_token,
                        "message": f"数据量较大（共{total_count}条），点击下载完整数据"
                    }
                
                return {"success": True, "action": action, "entity": entity, "data": records, "full_data": records, "total": total_count}
            
            elif action == "create":
                record = self._db.create(entity, data)
                return {"success": True, "action": action, "entity": entity, "data": record, "message": "创建成功"}
            
            elif action == "update":
                record_id = where.get("id")
                if record_id:
                    # 按 id 更新
                    record = self._db.update(entity, record_id, data)
                    return {"success": True, "action": action, "entity": entity, "data": record, "message": "更新成功"}
                elif records:
                    # 按条件更新
                    if len(records) == 1:
                        # 只有一条匹配，直接更新
                        result = self._db.update(entity, records[0].get("id"), data)
                        return {"success": True, "action": action, "entity": entity, "data": result, "message": "更新成功"}
                    else:
                        # 多条匹配，提示用户
                        return {"success": False, "error": f"找到 {len(records)} 条匹配记录，请指定更精确的条件或使用 id"}
                return {"success": False, "error": "未找到符合条件的记录"}
            
            elif action == "delete":
                record_id = where.get("id")
                if record_id:
                    if self._db.delete(entity, record_id):
                        return {"success": True, "action": action, "entity": entity, "message": "删除成功", "count": 1}
                    return {"success": False, "error": "记录不存在"}
                elif where:
                    deleted_count = 0
                    for record in records:
                        if self._db.delete(entity, record.get("id")):
                            deleted_count += 1
                    return {"success": True, "action": action, "entity": entity, "message": "批量删除成功", "count": deleted_count}
                return {"success": False, "error": "删除需要指定条件"}
            
            elif action == "aggregate" or action == "count":
                return {"success": True, "action": "aggregate", "type": "count", "entity": entity, "total": len(records)}
            
            return {"success": False, "error": f"不支持的操作: {action}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _resolve_step_references(self, step: dict, step_results: dict) -> dict:
        """解析步骤中的引用（如 $1.id）"""
        import re
        resolved = step.copy()
        if "where" in resolved and isinstance(resolved["where"], dict):
            new_where = {}
            for k, v in resolved["where"].items():
                if isinstance(v, str) and v.startswith("$"):
                    match = re.match(r'\$(\d+)\.(\w+)', v)
                    if match:
                        ref = step_results.get(int(match.group(1)), {}).get("data", [])
                        new_where[k] = ref[0].get(match.group(2)) if ref else None
                    else:
                        new_where[k] = v
                else:
                    new_where[k] = v
            resolved["where"] = new_where
        return resolved
    
    def _resolve_subqueries(self, where: dict) -> dict:
        """
        递归解析子查询条件，支持嵌套子查询
        """
        if not isinstance(where, dict):
            return where
        
        resolved = {}
        for key, value in where.items():
            if isinstance(value, dict) and "subquery" in value:
                sub_entity = value.get("subquery")
                sub_field = value.get("field", "id")
                sub_condition = value.get("condition", {})
                
                # 递归解析嵌套的子查询条件
                resolved_sub_condition = self._resolve_subqueries(sub_condition)
                print(f"[SDK] 子查询: SELECT {sub_field} FROM {sub_entity} WHERE {resolved_sub_condition}")
                
                # 执行子查询
                sub_records, sub_total = self._db.list(sub_entity, {}, limit=1000)
                
                # 过滤子查询结果
                for sub_key, sub_value in resolved_sub_condition.items():
                    if sub_value is not None:
                        if isinstance(sub_value, list):
                            sub_records = [r for r in sub_records if r.get(sub_key) in sub_value]
                        else:
                            sub_records = [r for r in sub_records if r.get(sub_key) == sub_value]
                
                print(f"[SDK] 子查询返回: {len(sub_records)}条记录")
                sub_ids = [r.get(sub_field) for r in sub_records if r.get(sub_field) is not None]
                print(f"[SDK] 提取的IDs: {sub_ids[:10]}...")  # 只打印前10个
                resolved[key] = sub_ids if sub_ids else None
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_foreign_keys(self, entity: str, records: list) -> list:
        """
        解析外键，将ID替换为名称
        从Schema中动态读取外键关系
        """
        if not records or not self._cached_schema:
            return records
        
        # 从Schema中获取当前实体的字段定义
        entities = self._cached_schema.get("entities", [])
        entity_def = next((e for e in entities if e.get("name") == entity), None)
        if not entity_def:
            return records
        
        # 查找外键字段（字段名以Id结尾，且有对应的实体表）
        fields = entity_def.get("fields", [])
        entity_names = [e.get("name") for e in entities]
        
        fk_fields = {}
        for field in fields:
            field_name = field.get("name", "")
            # 检查是否是外键（以Id结尾）
            if field_name.endswith("Id"):
                ref_table = field_name[:-2].lower()  # classId -> class
                if ref_table in entity_names:
                    # 获取引用表的显示字段（优先使用name字段）
                    ref_entity = next((e for e in entities if e.get("name") == ref_table), None)
                    if ref_entity:
                        ref_fields = ref_entity.get("fields", [])
                        display_field = "name" if any(f.get("name") == "name" for f in ref_fields) else "id"
                        # 优先使用字段的label，其次使用引用表的chinese_name，最后使用表名
                        label = field.get("label") or ref_entity.get("chinese_name", "").replace("表", "") or ref_table
                        fk_fields[field_name] = (ref_table, display_field, label)
        
        if not fk_fields:
            return records
        
        # 缓存外键表数据
        fk_cache = {}
        for fk_field, (ref_table, display_field, label) in fk_fields.items():
            try:
                ref_records, _ = self._db.list(ref_table, {}, limit=1000)
                fk_cache[fk_field] = {r.get("id"): r.get(display_field, f"未知") for r in ref_records}
            except:
                fk_cache[fk_field] = {}
        
        # 替换外键为名称
        result = []
        for record in records:
            new_record = {}
            for k, v in record.items():
                if k in fk_fields:
                    ref_table, display_field, label = fk_fields[k]
                    new_record[label] = fk_cache.get(k, {}).get(v, f"未知")
                else:
                    new_record[k] = v
            result.append(new_record)
        
        return result
    
    def _export_to_excel(self, entity: str, records: list) -> str:
        """导出数据到Excel文件，表头使用中文label"""
        import os
        import tempfile
        import csv
        from datetime import datetime
        
        if not records:
            return None
        
        # 透视成绩数据（如果是成绩数据）
        records = self._pivot_score_data(records)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{entity}_{timestamp}.csv"
        export_dir = self._export_dir or tempfile.gettempdir()
        filepath = os.path.join(export_dir, filename)
        
        # 常用字段的中文映射（通用）
        field_labels = {
            "name": "姓名", "age": "年龄", "gender": "性别", "phone": "手机号码",
            "status": "状态", "createdAt": "创建时间", "updatedAt": "更新时间",
            "grade": "年级", "teacher": "班主任", "score": "分数", "semester": "学期",
            "credit": "学分", "address": "地址", "email": "邮箱", "birthday": "生日"
        }
        # 从Schema获取字段的label（如果有定义）
        if self._cached_schema:
            entities = self._cached_schema.get("entities", [])
            entity_def = next((e for e in entities if e.get("name") == entity), None)
            if entity_def:
                for field in entity_def.get("fields", []):
                    if field.get("label"):
                        field_labels[field.get("name", "")] = field.get("label")
        
        # 获取表头（排除id字段）
        original_headers = [k for k in records[0].keys() if k.lower() != 'id']
        cn_headers = [field_labels.get(h, h) for h in original_headers]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(cn_headers)
            for record in records:
                row = []
                for h in original_headers:
                    v = record.get(h, '')
                    if hasattr(v, 'strftime'):
                        row.append(v.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        row.append(v)
                writer.writerow(row)
        
        print(f"[SDK] 已导出Excel: {filepath}, 共{len(records)}条记录")
        return filepath
    
    def _serialize(self, obj):
        """序列化对象，处理 datetime 等类型"""
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize(i) for i in obj]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return obj
    
    # ============ 上下文管理器 ============
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """关闭连接"""
        self._session.close()
    
    @property
    def is_registered(self) -> bool:
        """是否已注册 Schema"""
        return self._schema_registered
    
    @property
    def entities(self) -> List[str]:
        """已注册的实体列表"""
        return self._entities
    
    @property
    def conversation_id(self) -> Optional[str]:
        """当前对话 ID"""
        return self._conversation_id
    
    # ============ 内置 HTTP 服务器 ============
    
    def run_server(self, host: str = "0.0.0.0", port: int = 8000, cors_origins: List[str] = None):
        """
        启动内置 HTTP 服务器
        
        Args:
            host: 监听地址，默认 0.0.0.0
            port: 端口，默认 8000
            cors_origins: 允许的跨域来源，默认 ["*"]
        
        Example:
            client = AIAgentClient(api_key="...", db_config={...})
            client.run_server(port=8000)
        """
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import StreamingResponse, JSONResponse
            from fastapi.middleware.cors import CORSMiddleware
            from pydantic import BaseModel
            import uvicorn
        except ImportError:
            raise ImportError("请安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
        
        app = FastAPI(title="AI Agent API", version="1.0.0")
        
        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 请求模型
        class ChatRequest(BaseModel):
            message: str
            history: List[Dict] = []
        
        class ConfirmRequest(BaseModel):
            steps: List[Dict]
            original_message: str
        
        class SchemaRequest(BaseModel):
            system_name: str = ""
            entities: List[Dict] = []
        
        class GenerateRequest(BaseModel):
            use_ai: bool = False
        
        # 流式对话
        @app.post("/api/chat/stream")
        async def chat_stream(request: ChatRequest):
            def generate():
                for event in self.process_chat_stream(request.message, request.history):
                    yield event
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        # 确认执行
        @app.post("/api/chat/confirm")
        async def chat_confirm(request: ConfirmRequest):
            result = self.execute_steps(request.steps, request.original_message)
            return {"success": True, "message": result.get("message", "")}
        
        # 普通对话
        @app.post("/api/chat")
        async def chat(request: ChatRequest):
            result = self.ask_and_execute(request.message, request.history)
            return result
        
        # 获取 Schema
        @app.get("/api/schema")
        async def get_schema():
            return {"schema": self.get_schema()}
        
        # 注册 Schema
        @app.post("/api/schema/register")
        async def register_schema_api(request: SchemaRequest):
            self.register_schema(request.entities, system_name=request.system_name)
            return {"success": True, "message": "Schema 注册成功"}
        
        # 生成 Schema
        @app.post("/api/schema/generate")
        async def generate_schema(request: GenerateRequest):
            result = self.generate_schema_from_db(use_ai=request.use_ai)
            return {"entities": result.get("entities", [])}
        
        # 检查 Schema 完整性
        @app.get("/api/schema/check")
        async def check_schema():
            return self.check_schema_completeness()
        
        print(f"🚀 AI Agent 服务已启动: http://{host}:{port}")
        print(f"📖 API 文档: http://{host}:{port}/docs")
        uvicorn.run(app, host=host, port=port)
