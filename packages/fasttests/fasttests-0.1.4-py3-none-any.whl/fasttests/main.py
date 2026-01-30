import __main__
import json
import pkgutil
import re
import ssl
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from functools import cached_property
from io import TextIOWrapper
from pathlib import Path
from typing import Literal, Callable, ClassVar, TypedDict


class Env(TypedDict):
    dev__user__admin__login: str
    dev__user__admin__password: str
    dev__user__regmn__login: str
    dev__user__regmn__password: str
    dev__app__domain: str
    dev__app__isso_url: str
    dev__app__client_id: str
    dev__app__client_secret: str


class Paths(TypedDict):
    path: str
    autotest: str
    tests: str
    params: str
    swagger: str
    swagger_endpoints: str
    swagger_schemas: str
    browser: str
    browser_pages: str
    browser_components: str
    params_api: str
    params_ui: str
    tests_test_api: str
    tests_test_ui: str


@dataclass
class Component:
    component: str = None
    unique: bool = False


@dataclass
class Page:
    name: str = None
    url: str = None
    components: list[Component] = field(default_factory=list)


@dataclass
class Line:
    line: list
    path: str


@dataclass(frozen=True)
class Names:
    mode: Literal['tag', 'endpoint', 'schema']
    name: str = None
    name_snake: str = None
    name_camel: str = None

    def __post_init__(self):
        object.__setattr__(self, 'name', self.__set_name(self.name))
        object.__setattr__(self, 'name_snake', self.__set_name_snake())
        object.__setattr__(self, 'name_camel', self.__set_name_camel())

    def __set_name(self, attr: dict | str):
        if self.mode == 'tag':
            # return list(set([value for keys, values in attr.items() for value in values.get('tags', ['Default'])]))[0]
            return [value for keys, values in attr.items() for value in values.get('tags', ['Default'])][0]
        if self.mode == 'endpoint':
            return attr
        if self.mode == 'schema':
            if isinstance(attr, str):
                return attr
            return name.split('/')[-1] if (name := Text.find(attr, '$ref')) != None else None
    
    def __set_name_snake(self):
        if self.mode == 'tag':
            return f'{Text.to_snake_case(self.name)}_endpoint'
        if self.mode == 'endpoint':
            return f'{Text.to_snake_case(self.name.replace("/api/v1/", "").replace("/api/", "").replace("/", "_").replace("{", "").replace("}", ""))}'
        if self.mode == 'schema':
            return Text.to_snake_case(self.name) if self.name != None else None
    
    def __set_name_camel(self):
        if self.mode == 'tag':
            return f'{Text.to_camel_case(self.name)}Endpoint'
        if self.mode == 'endpoint':
            return f'{Text.to_camel_case(self.name.replace("/", "_").replace("{", "").replace("}", ""))}'
        if self.mode == 'schema':
            return self.name if self.name != None else None


@dataclass
class Parameter:
    param: Literal["path", "query"] = None
    alias: str = None
    type: str = None

    def __post_init__(self):
        self.param = self.set_param(self.param)
        self.alias = self.set_alias(self.alias)
        self.name = self.set_name(self.alias)
        self.type = self.set_type(self.type)

    def set_param(self, attr: dict):
        return attr["in"]
    
    def set_alias(self, attr: dict):
        return attr["name"]
    
    def set_name(self, attr: str):
        return attr.replace(".", "_")
    
    def set_type(self, attr: dict):
        return Text.to_python_type(attr["schema"]["type"])


@dataclass
class Props:
    name: str = None
    type: str = None
    schema: str = None
    schema_snake: str = None

    def __post_init__(self):
        self.schema = self.set_schema(self.schema)
        self.schema_snake = self.set_schema_snake()
        self.type = self.set_type(self.type)

    def set_schema(self, attr: dict):
        if (schema := Text.find(attr, '$ref')) != None:
            return schema.split('/')[-1]
        
    def set_schema_snake(self):
        if self.schema != None:
            return Text.to_snake_case(self.schema)

    def set_type(self, attr: dict):
        return ' | '.join(
            [Text.to_python_type(_.get("type")) if _.get("type") != None and _.get("items") == None else
            _.get("$ref").split('/')[-1] if _.get("type") == None and _.get("$ref") != None else 
            f'{Text.to_python_type(_.get("type"))}[{Text.to_python_type(_.get("items").get("type"))}]' if _.get("type") != None and _.get("items").get("type") != None else
            f'{Text.to_python_type(_.get("type"))}[{_.get("items").get("$ref").split('/')[-1]}]' if _.get("type") != None and _.get("items").get("$ref") != None else None for _ in attr.get("oneOf", [attr])] + 
            ['None' for _ in attr.get("oneOf", [attr]) if _.get("nullable") == True]
        )
    

@dataclass
class Schema:
    status: str = None
    names: Names = None
    schema_type: str = None
    body_type: Literal["request", "response"] = None
    content_type: str = None
    properties: list[Props] = None

    def __post_init__(self):
        self.content_type = self.set_content_type(self.content_type)
        self.schema_type = self.set_schema_type(self.schema_type)
    
    def set_content_type(self, attr: dict):
        if self.content_type != None:
            return ''.join(content_type.keys()) if (content_type := Text.find(attr, 'content')) != None else None
        
    def set_schema_type(self, attr: dict):
        if self.schema_type != None:
            return Text.to_python_type(schema_type.get('type')) if (schema_type := Text.find(attr, 'schema')) != None else None


@dataclass   
class Method:
    name: str = None
    schemas: list[Schema] = None
    parameters: list[Parameter] = None


@dataclass(frozen=True)
class Endpoint:
    names: Names = None
    tags: Names = None
    methods: list[Method] = None


@dataclass
class Configuration:
    """
    - ui: bool True if you need to generate UI tests else False
    - api: ClassVar[str] = path to API tests in JSON format
    - paths: ClassVar[Paths] It is recommended not to change the file and directory generation paths
    - env: ClassVar[Env] The environment parameters on the basis of which tests are carried out, as an example, the parameters for authorization through isso with two different users are left. For the script, it is important that the key name between logical blocks contains two underscores
    - pages: ClassVar[list[Page]] Description of pages, consists of the page name, URL, and the component being used. A template will be used as an example
    - open_api: calculated value based on cls.api
    - environments: calculated value based on cls.env
    - endpoints: calculated value based on cls.api
    - schemas: calculated value based on cls.api
    """
    ui: bool = False
    api: ClassVar[str] = ""
    paths: ClassVar[Paths] = {
        "path": f'{Path(__main__.__file__).parent}/'.replace("\\", "/"),
        "autotest": "autotest/",
        "swagger": "autotest/swagger/",
        "swagger_endpoints": "autotest/swagger/endpoints/",
        "swagger_schemas": "autotest/swagger/schemas/",
        "browser": "autotest/browser/",
        "browser_pages": "autotest/browser/pages/",
        "browser_components": "autotest/browser/components/",
        "params": "autotest/params/",
        "params_api": "autotest/params/api/",
        "params_ui": "autotest/params/ui/",
        "tests": "autotest/tests/",
        "tests_test_api": "autotest/tests/test_api/",
        "tests_test_ui": "autotest/tests/test_ui/"
    }
    env: ClassVar[Env] = {
        "dev__user__admin__login": "",
        "dev__user__admin__password": "",
        "dev__user__regmn__login": "",
        "dev__user__regmn__password": "",
        "dev__app__domain": "",
        "dev__app__isso_url": "",
        "dev__app__client_id": "",
        "dev__app__client_secret": ""
    }
    pages: ClassVar[list[Page]] = None
    """
    ```python
    from fasttests import FastTest, Page, Component

    test = FastTest()

    test.configuration.pages = [
        Page(
            name='main',
            url='',
            components=[
                Component(component='table', unique=True),
                Component(component='menu', unique=False)
            ]
        )
    ]
    ```
    """

    @cached_property
    def open_api(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return json.loads(urllib.request.urlopen(url=urllib.request.Request(self.api), context=context).read().decode('UTF-8'))
    
    @cached_property
    def environments(self) -> dict:
        def add_dict_env(env_dict: dict, env_list: list, env_str: str):
            """
            Создать список с переменными окружения 
                - env_dict: словарь для добавления новых переменных
                - env_list: список ключей для создания вложенности
                - env_str: имя переменной окружения
            """
            if len(env_list) != 1:
                env_dict.setdefault(env_list[0], {})
                add_dict_env(env_dict[env_list[0]], env_list[1:], env_str)
            else:
                env_dict.setdefault(env_list[0], env_str)
        self._environments = {}
        for name_env in self.env:
            add_dict_env(self._environments, name_env.split('__'), name_env.upper())           
        return self._environments
  
    @cached_property
    def endpoints(self) -> list[Endpoint]:
        return [
            Endpoint(
                names=Names(
                    mode='endpoint',
                    name=endpoint
                ),
                tags=Names(
                    mode='tag',
                    name=endpoint_values
                ),
                methods=[
                    Method(
                        name=method,
                        parameters=[
                            Parameter(
                                alias=parameter,
                                param=parameter,
                                type=parameter
                            ) for parameter in method_values.get("parameters")
                        ] if method_values.get("parameters") != None else None,
                        schemas=[__ for _ in [[
                            Schema(
                                body_type="response",
                                content_type=method_values.get("responses")[status],
                                schema_type=method_values.get("responses")[status],
                                status=status,
                                names=Names(
                                    mode='schema',
                                    name=method_values.get("responses")[status]
                                ),
                                properties=[
                                    Props(
                                        name=props,
                                        type=props_values,
                                        schema=props_values
                                    ) for props, props_values in Text.find(method_values.get("responses")[status], "properties").items()
                                # ] if Text.find(method_values.get("responses")[status], '$ref') == None and Text.find(method_values.get("responses")[status], "properties") != None else None
                                ] if Text.find(method_values.get("responses")[status], "properties") != None else None
                            ) for status in method_values.get("responses")
                        ] if method_values.get("responses") != None else []] + [[
                            Schema(
                                body_type="request",
                                content_type=method_values.get("requestBody"),
                                schema_type=method_values.get("requestBody"),
                                names=Names(
                                    mode='schema',
                                    name=method_values.get("requestBody")
                                ),
                                properties=[
                                    Props(
                                        name=props,
                                        type=props_values,
                                        schema=props_values
                                    ) for props, props_values in Text.find(method_values.get("requestBody"), "properties").items()
                                # ] if Text.find(method_values.get("requestBody"), '$ref') == None and Text.find(method_values.get("requestBody"), "properties") != None else None
                                ] if Text.find(method_values.get("requestBody"), "properties") != None else None
                            )
                        ] if method_values.get("requestBody") != None else []] for __ in _]
                    ) for method, method_values in endpoint_values.items()]
            ) for endpoint, endpoint_values in self.open_api["paths"].items()]

    @cached_property
    def schemas(self) -> list[Schema]:
        return [
            Schema(
                names=Names(
                    mode='schema',
                    name=schema
                ),
                properties=[
                    Props(
                        name=props,
                        type=props_values,
                        schema=props_values
                    ) for props, props_values in schema_values.get("properties").items()
                ] if schema_values.get("properties") != None else None
            ) for schema, schema_values in self.open_api["components"]["schemas"].items()] if self.open_api["components"].get("schemas") != None else []

    @cached_property
    def tags(self) -> list[Names]:
        return list({_.tags for _ in self.endpoints}) 


class Text:

    @classmethod
    def to_comment_line(cls, text: str) -> str:
        return f'# {"=" * int((79 - len(text)) / 2)} {text} {"=" * int((79 - len(text)) / 2)}\n'

    @classmethod
    def to_python_type(cls, text: str) -> str:
        return {
            "string": "str",
            "number": "float",
            "array": "list",
            "integer": "int",
            "boolean": "bool",
            "object": "dict"
        }.get(text)
    
    @classmethod
    def find(cls, data: dict, text: str) -> str | dict | None:
        for _ in data:
            if _ == text:
                return data[_]
            if isinstance(data[_], dict):
                if (__ := cls.find(data[_], text)) != None:
                    return __

    @classmethod
    def to_snake_case(cls, text: str) -> str:
        """Преобразует текст в snake_case"""
        text = re.sub(r'[\s-]+', '_', text)  # Заменяем пробелы и дефисы на подчеркивания
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)  # Вставляем подчеркивания между строчными и прописными буквами
        text = re.sub(r'_+', '_', text)  # Заменяем несколько подчеркиваний на одно
        return text.strip().lower()  # Приводим к нижнему регистру и убираем пробелы по краям

    @classmethod
    def to_camel_case(cls, text: str) -> str:
        """Преобразует текст в camelCase"""
        text = re.sub(r'[\s\-_]+', ' ', text)  # Заменяем пробелы, дефисы, подчеркивания на пробелы  
        text = text.strip().split()  # Разбиваем на слова   
        text = ''.join([_.capitalize() for _ in text])  # Объединяем слова с заглавной буквой
        return text


class Matrix:

    @classmethod
    def packing(cls, lines: str):
        return [[_.splitlines(keepends=True) for _ in re.split(r'(?<=\n)\n(?=[^\n])', line)] for line in re.split(r'(?<=\n)\n{2}(?=[^\n])', lines)]

    @classmethod
    def unpacking(cls, lines: list, types: Literal["str", "list"] = "list", filters: Callable = lambda _: _):
        flag_1, flag_2, last = True, True, ''
        def auto_replace(line: str):
            nonlocal flag_1, flag_2, last
            while line.count('\n') > 0:
                line = line.replace('\n', '')
            if any([
                line[:1] == '#' and flag_1,
                line[:5] == '    @' and last[:5] != '    @' and flag_1,
                line[:10] == '    class ' and flag_1,
                line[:8] == '    def ' and last[:5] != '    @' and flag_1,
                line[:14] == '    async def ' and last[:5] != '    @' and flag_1,
                line[:10] == '    PARAM_' and flag_1
            ]):
                last, flag_1, flag_2 = line, False, True
                return '\n' + line + '\n'
            elif any([
                line[:1] == '@' and last[:1] != '@' and flag_2,
                line[:6] == 'class ' and last[:1] != '@' and flag_2,
                line[:4] == 'def ' and flag_2,
                line[:10] == 'async def ' and flag_2
            ]):
                last, flag_1, flag_2 = line, True, False
                return '\n\n' + line + '\n'
            else:
                last, flag_1, flag_2 = line, True, True
                return line + '\n'
        def auto_unpacking(lines: list[str]):
            __ = []
            for line in lines:
                if isinstance(line, list):
                    __.extend(auto_unpacking(line))
                else:
                    if line.strip() and filters(line): 
                        __.append(auto_replace(line)) 
            return __
        if types == "list":
            return auto_unpacking(lines)
        elif types == "str":
            return ''.join(auto_unpacking(lines)).strip() + '\n'

    @classmethod
    def find_point(cls, lines: list, key: str, point: list = None):
        if point == None:
            point = []
        if isinstance(lines, list):
            for _, line in enumerate(lines):
                if (__ := cls.find_point(line, key, point + [_])) is not None:
                    return __
        elif key in lines:
            return point


class File:

    LIBS = [name for path, name, _ in pkgutil.iter_modules() if 'Python3'in str(path)]

    def __init__(self, file: TextIOWrapper):
        self.__file = file

    @property
    def depends(self) -> list:
        if self.__dict__.get('_depends') == None:
            self._depends = []
        return self.__dict__.get('_depends')
    
    @depends.setter
    def depends(self, lines: list[str]):
        def check(line: str):
            return all([
                line not in ['# Standard library\n', '# Installed libraries\n', '# Local imports\n'],
                line[0] != '@',
                line[:4] != 'def ',
                line[:5] != 'from ',
                line[:6] != 'class ',
                line[:6] != 'async ',
                line[:7] != 'import ',
                line[:5] != '     ',
                line[:5] != '    @',
                line[:8] != '    def ',
                line[:10] != '    class ',
                line[:10] != '    async ',
                line[:11] != '    return ',
            ])
        lines = Matrix.packing(Matrix.unpacking(lines, types="str"))
        if (point := Matrix.find_point(lines, 'class ')) != None:
            lines = lines[:point[0]]
        elif (point := Matrix.find_point(lines, 'def ')) != None:
            lines = lines[:point[0]]
        self._depends = Matrix.packing(Matrix.unpacking(lines, types="str", filters=check))
            
    @property
    def imports(self) -> list:
        if self.__dict__.get('_imports') == None:
            if (point := Matrix.find_point(self.lines, 'import')) != None:
                self._imports = [self.lines[point[0]]]
        return [[
            sorted(list(filter(lambda _: 'from' not in _, ___))) +
            sorted(list(filter(lambda _: 'from' in _, ___)))
            for __ in self.__dict__.get('_imports', []) for ___ in __
        ]]

    @imports.setter
    def imports(self, lines: list[str]):
        if (lines := list(filter(lambda _: 'import ' in _ and _[0] != ' ' in _, Matrix.unpacking(self.imports + lines)))) == []:
            self._imports = lines
        else:
            __ = [
                ['# Standard library\n'],
                ['# Installed libraries\n'],
                ['# Local imports\n']
            ]
            for _ in list(set(lines)):
                if _.split()[1] in self.LIBS:
                    __[0].append(_)
                elif Configuration.paths['autotest'][:-1] in _:
                    __[2].append(_)
                elif '#' not in _:
                    __[1].append(_)
            self._imports = [[_ for _ in __ if len(_) > 1]]

    @property
    def classes(self) -> list:
        if self.__dict__.get('_classes') == None:
            if (point := Matrix.find_point(self.lines, 'class ')) != None:
                self._classes = self.lines[point[0]:]
        return [[
            _[0],
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' class') != None, _[1:])), 
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'class')[0]])[0]),
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' def') != None, _[1:])),
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'def')[0]])[0]),
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' PARAM_') != None, _[1:])),
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'PARAM_')[0]])[0])
        ] for _ in self.__dict__.get('_classes', [])]

    @classes.setter
    def classes(self, lines: list):
        if Matrix.find_point(lines, 'class ') != None:
            for lines in Matrix.packing(Matrix.unpacking(lines, types="str"))[Matrix.find_point(Matrix.packing(Matrix.unpacking(lines, types="str")), 'class ')[0]:]:
                name = re.findall(r'\s(\w+)[^\w\s]', ''.join([_ for _ in lines[0] if 'class' in _]))[0]
                point = Matrix.find_point([[_[0]] for _ in self.classes], f'{name}:') or Matrix.find_point([[_[0]] for _ in self.classes], f'{name}(')
                if point == None:
                    self._classes = self.__dict__.get('_classes', []) + [lines]
                else:
                    for line in lines[1:]:
                        _name: str = re.findall(r'\s(\w+)[^\w\s]', ''.join(line))[0]
                        _point = Matrix.find_point(self._classes[point[0]], _name)
                        if _point == None:
                            self._classes[point[0]] += [line]
                        elif (not _name.islower() and not _name.isupper()) or (_name == '__init__' and Matrix.find_point(self._classes[point[0]], '__init__(self, client:') != None):
                            self._classes[point[0]][_point[0]] = line

    @property
    def funcs(self) -> list:
        if self.__dict__.get('_funcs') == None:
            if Matrix.find_point(self.lines, 'class ') == None:
                point = [point[0] for point in [Matrix.find_point(self.lines, 'def '), Matrix.find_point(self.lines, 'async def ')] if point != None]
                if len(point) != 0:
                    self._funcs = self.lines[min(point):]
        return self.__dict__.get('_funcs', [])

    @funcs.setter
    def funcs(self, lines: list):
        if Matrix.find_point(lines, 'class ') == None:
            lines = Matrix.packing(Matrix.unpacking(lines, types='str'))
            point = [point[0] for point in [Matrix.find_point(lines, 'def '), Matrix.find_point(lines, 'async def ')] if point != None]
            if len(point) != 0:
                self._funcs = lines[min(point):]

    @property
    def lines(self) -> list:
        if self.__dict__.get('_lines') == None:
            self.__file.seek(0)
            if (lines := self.__file.readlines()) != []:
                self._lines = Matrix.packing(Matrix.unpacking(lines, types="str"))
        return self.__dict__.get('_lines', [])

    @lines.setter
    def lines(self, lines: list):
        self.imports = lines
        self.depends = lines
        self.classes = lines
        self.funcs = lines
        self.__file.truncate(0)
        self.__file.write('\n\n'.join([
            line for line in
            [
                Matrix.unpacking(self.imports, types="str"),
                Matrix.unpacking(self.depends, types="str"),
                Matrix.unpacking(self.classes, types="str"),
                Matrix.unpacking(self.funcs, types="str")
            ] if line != '\n'
        ]))


class Creator:
    """
    ### File creation decorator

    
    A decorator for creating files based on a list of passed data, expecting two parameters, the type of file modification (complete overwrite or append) and a list of Line classes

    
    ### Args:
        mode (str): takes the value: 
            +a to append values to the file 
            +w to completely overwrite the file
        line (list[Line]) The Line class must be imported from the fasttests library and takes two parameters: 
            line (a list of required values for creating a file)
            path (a string containing the path to the created file)


    ### Examples

    ```python
    from fasttests import FastTests, Line

    test = FastTests()
    test.configuration.api = 'https:/portal/docs.json'

    @test.creator(
        mode='+w', 
        line=[Line(
            line=schema, 
            path=f'{schema.names.name_snake}.py') for schema in self.configuration.schemas
        ]
    )
    def create_schemas(line: Schema):
        paths = f'{self.configuration.paths["swagger_schemas"].replace("/", ".")}'
        return [
            'from pydantic import BaseModel',
            [
                f'from {paths}{props.schema_snake} import {props.schema}' 
                for props in list(filter(lambda _: _.schema != None, line.properties))
            ],
            f'class {line.names.name_camel}(BaseModel):',
            [f'    {props.name}: {props.type} = None' for props in line.properties]
        ]
    ```
    """

    def __init__(self, *, mode: Literal['addition', 'creation', 'rewrite'], line: list[Line]):
    # def __init__(self, *, mode: Literal["+a", "+w", 'addition', 'creation', 'rewrite'], line: list[Line]):
        self.configuration = Configuration()
        self.mode = mode
        self.line = line

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            for _ in self.line:
                Path(f'{self.configuration.paths['path']}{'/'.join(_.path.split('/')[:-1])}').mkdir(exist_ok=True, parents=True)
                if Path(f'{self.configuration.paths['path']}{_.path}').exists() and self.mode == 'creation':
                    continue
                with open(f'{self.configuration.paths['path']}{_.path}', '+a' if self.mode == 'addition' else '+w', encoding="UTF-8") as file:
                    file = File(file)
                    file.lines = func(line=_.line, *args, **kwargs)
        return wrapper


class Create:
    
    def __init__(self, configuration = None):
        self.configuration = Configuration() if configuration == None else configuration
        self.creator = Creator

    def set_endpoints(self):
        @self.creator(mode='addition', line=[Line(line=list(filter(lambda __: __.tags.name == _.name, self.configuration.endpoints)), path=f'{self.configuration.paths["swagger_endpoints"]}{_.name_snake}.py') for _ in self.configuration.tags])
        def wrapper(line: list[Endpoint]):
            return [
                'from httpx import AsyncClient',
                'from pydantic import BaseModel, Field, TypeAdapter',
                [f'from {self.configuration.paths["swagger_schemas"].replace("/", ".")}{schema.names.name_snake} import {schema.names.name_camel}'  for endpoint in line for method in endpoint.methods for schema in method.schemas if schema.names.name != None],
                f'class {line[0].tags.name_camel}:',
                '    def __init__(self, client):',
                [f'        self.{endpoint.names.name_snake} = {endpoint.names.name_camel}(client)' for endpoint in line],
                [[f'class {endpoint.names.name_camel}:',
                [[f'    class {method.name.capitalize() + "Params"}(BaseModel):',
                [f'        {parameter.name}: {parameter.type} = Field(None, alias=\'{parameter.alias}\')' for parameter in list(filter(lambda _: _.param == "query", method.parameters))]] for method in endpoint.methods if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0],
                [[f'    class {method.name.capitalize()}RequestBody(BaseModel):',
                # [f'        {props.name}: {props.type} = None' for props in schema.properties]] for method in endpoint.methods for schema in method.schemas if schema.names.name == None and schema.properties != None and schema.body_type == "request"],
                [f'        {props.name}: {props.type} = None' for props in schema.properties]] for method in endpoint.methods for schema in method.schemas if schema.properties != None and schema.body_type == "request"],
                [[f'    class {method.name.capitalize()}Status{schema.status}(BaseModel):',
                # [f'        {props.name}: {props.type}' for props in schema.properties]] for method in endpoint.methods for schema in method.schemas if schema.names.name == None and schema.properties != None and schema.body_type != "request"],
                [f'        {props.name}: {props.type}' for props in schema.properties]] for method in endpoint.methods for schema in method.schemas if schema.properties != None and schema.body_type != "request"],
                '    def __init__(self, client: AsyncClient):', 
                '        self.__client = client',
                f'        self.__url = \'{endpoint.names.name}\'',
                [f'        self.body_{method.name} = {request[0].names.name}()' if request[0].names.name != None else f'        self.body_{method.name} = {endpoint.names.name_camel}.{method.name.capitalize()}RequestBody()' for method in endpoint.methods if len(request := list(filter(lambda _: _.body_type == 'request' , method.schemas))) != 0],
                [f'        self.params = {endpoint.names.name_camel}.{method.name.capitalize() + "Params"}()' for method in endpoint.methods if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0],
                [[f'    async def {method.name}(self{', ' + ', '.join([f'{parameter.name}: {parameter.type}' for parameter in list(filter(lambda _: _.param == "path", method.parameters))]) if method.parameters != None and len(list(filter(lambda _: _.param == "path", method.parameters))) != 0 else ''}):',
                f'        response = await self.__client.{method.name}(',
                [f'            self.__url{'.replace(' + '.replace('.join([f'\'{{{parameter.name}}}\', str({parameter.name}))' for parameter in list(filter(lambda _: _.param == "path", method.parameters))]) if method.parameters != None and len(list(filter(lambda _: _.param == "path", method.parameters))) != 0 else ''},',],
                [f'            headers={{\'Content-Type\': \'{schema.content_type}\'}},' for schema in list(filter(lambda _: _.body_type == "response" and 200 <= int(_.status) < 300 , method.schemas)) if schema.content_type != None],
                [f'            data = self.body_{method.name}.model_dump_json(),'] if len(request := list(filter(lambda _: _.body_type == 'request' , method.schemas))) != 0 else [],
                [f'            params = self.params.model_dump(exclude_none=True, by_alias=True),'] if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0 else [],
                f'        )',
                [[f'        if response.status_code == {schema.status}:',
                # f'            self.response = {endpoint.names.name_camel}.{method.name.capitalize() + "Status" + schema.status}(**response.json())' if schema.names.name == None else 
                # f'            self.response = {schema.names.name}(**response.json())',] for schema in method.schemas if schema.status != None and (schema.names.name != None or schema.properties != None)],
                f'            self.response = {endpoint.names.name_camel}.{method.name.capitalize() + "Status" + schema.status}.model_validate(response.json())' if schema.properties != None else 
                f'            self.response = {schema.names.name}.model_validate(response.json())' if schema.schema_type == None else
                f'            self.response = TypeAdapter({schema.schema_type}[{schema.names.name}]).validate_python(response.json())',] for schema in method.schemas if schema.status != None and (schema.names.name != None or schema.properties != None)],
                f'        return response'] for method in endpoint.methods]] for endpoint in line]
            ]
        wrapper()

    def set_schemas(self):
        @self.creator(mode='rewrite', line=[Line(line=schema, path=f'{self.configuration.paths["swagger_schemas"]}{schema.names.name_snake}.py') for schema in self.configuration.schemas])
        def wrapper(line: Schema):
            return [
                'from pydantic import BaseModel\n',
                [f'from {self.configuration.paths["swagger_schemas"].replace("/", ".")}{props.schema_snake} import {props.schema}' for props in list(filter(lambda _: _.schema != None, line.properties))],
                f'class {line.names.name_camel}(BaseModel):\n',
                [f'    {props.name}: {props.type} = None\n' for props in line.properties]
            ]
        wrapper()

    def set_conftest_api(self):
        @self.creator(mode='addition', line=[Line(line=self.configuration.environments, path=f'{self.configuration.paths["tests"]}conftest.py')])
        def wrapper(line):
            return [
                'import pytest',
                'from httpx import AsyncClient',
                'from dotenv import load_dotenv',
                f'from {self.configuration.paths["swagger"].replace("/", ".")}blank_client import BlankClient',
                'load_dotenv()',
                '@pytest.fixture(scope="session")',
                'def environments():',
                f'    return {line}',
                '@pytest.fixture(scope="session", autouse=True)',
                'async def token(environments):',
                '    async with AsyncClient(verify=False) as client:',
                '        client = BlankClient(client)',
                '        await client.create_token(environments)',
                '@pytest.fixture(scope="function")',
                'async def client():',
                '    async with AsyncClient(verify=False) as client:',
                '        client = BlankClient(client)',
                '        yield client'
            ]
        wrapper()
        
    def set_conftest_ui(self):
        @self.creator(mode='rewrite', line=[Line(line=self.configuration.environments, path=f'{self.configuration.paths["tests_test_ui"]}conftest.py')])
        def wrapper(line):
            return [
                'import pytest',
                'import allure',
                'import shutil',
                'import os',
                'from pathlib import Path',
                'from playwright.async_api import async_playwright, Browser',
                f'from {self.configuration.paths["browser"].replace("/", ".")}blank_page import BlankPage',
                f'from {self.configuration.paths["swagger"].replace("/", ".")}blank_client import BlankClient',
                '@pytest.fixture(scope="session")',
                'async def browser():',
                '    async with async_playwright() as _:',
                '        browser = await _.chromium.launch(',
                '            args=[',
                '                \'--disable-gpu\',',
                '                \'--disable-dev-shm-usage\',',
                '                \'--disable-setuid-sandbox\',',
                '                \'--no-first-run\',',
                '                \'--no-sandbox\',',
                '                \'--no-zygote\',',
                '                \'--disable-web-security\',',
                '                \'--disable-features=VizDisplayCompositor\',',
                '                \'--disable-background-timer-throttling\',',
                '                \'--disable-renderer-backgrounding\',',
                '                \'--disable-backgrounding-occluded-windows\'',
                '            ],',
                '            # headless=False,',
                '            # slow_mo=500',
                '        )',
                '        yield browser',
                '        await browser.close()',
                '@pytest.fixture(scope="function")',
                'async def page(browser: Browser, request: pytest.FixtureRequest, environments):',
                '    params = request.node.name.split(\'[\')[-1].replace(\']\', \'\').split(\'-\')',
                f'    domain, user = set(params) & {set(line)}, set(params) & {set(line[list(line)[0]]["user"])}',
                '    domain = \'\'.join(domain) if len(domain) != 0 else \'dev\'',
                '    user = \'\'.join(user) if len(user) != 0 else \'admin\'',
                '    path = f\'{Path(__file__).parent.parent.parent}\\\\auth\\\\{domain}_{user}.json\'',
                '    Path(path).parent.mkdir(parents=True, exist_ok=True)',
                '    context = await browser.new_context(',
                '        viewport={\'width\': 1920, \'height\': 1080},',
                '        base_url=os.environ[environments["dev"]["app"]["domain"]],',
                '        storage_state=path if Path(path).exists() and \'auth\' not in request.node.name else None,',
                '        record_video_dir=f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{request.node.name}\\\\\',',
                '        ignore_https_errors=True,',
                '        java_script_enabled=True,',
                '        bypass_csp=True',
                '    )',
                '    page = await context.new_page()',
                '    yield BlankPage(page)',
                '    if \'auth\' in request.node.name:',
                '        await page.context.storage_state(path=path)',
                '    await page.close()',
                '    await context.close()',
                '@pytest.hookimpl(tryfirst=True, hookwrapper=True)',
                'def pytest_runtest_makereport(item: pytest.Item):',
                '    """Получаем отчет о выполнении теста и удаляем видео успешных тестов"""',
                '    def replace(lines: list, params: dict):',
                '        _ = []',
                '        def recursion(line: str, params: dict):',
                '            for param in params:',
                '                if isinstance(params[param], dict):',
                '                    return recursion(line, params[param])',
                '                return line.replace("{" + param + "}", str(params[param]))',
                '            for line in lines:',
                '                line = recursion(line, params)[8:]',
                '                if "{" not in line and "}" not in line:',
                '                    _.append(line)',
                '            return _',
                '    outcome = yield',
                '    report = outcome.get_result()',
                '    if report.when == "setup" and (doc := item.function.__doc__) != None:',
                '        doc = replace(doc.strip().split(\'\n\'), {"id": item.callspec.id} | item.callspec.params)',
                '        allure.dynamic.title(doc[0])',
                '        allure.dynamic.description("\n".join(doc[2:]))',
                '    if report.when == "call" and report.outcome == "passed":',
                '        shutil.rmtree(Path(f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{item.name}\\\\\'))'
            ]
        wrapper()

    def set_pytest(self):
        @self.creator(mode='rewrite', line=[Line(line={'api': self.configuration.tags, 'ui': self.configuration.pages}, path='pytest.ini')])
        def wrapper(line: dict[Literal["api", "ui"], list[Names | Page]]):
            return [
                '[pytest]',
                'pythonpath = . ',
                f'testspath = {self.configuration.paths["tests"]}',
                'disable_test_id_escaping_and_forfeit_all_rights_to_community_support = True',
                'max_asyncio_tasks = 8',
                # 'asyncio_default_fixture_loop_scope = function',
                'addopts = ',
                '    -m \'regression\'',
                '    -p no:pytest_asyncio',
                # '    -p no:pytest-xdist',
                f'    --alluredir={self.configuration.paths["path"]}{self.configuration.paths["autotest"]}results',
                '    --clean-alluredir',
                'markers = ',
                '    regression: регресс тесты',
                '    api: api тесты',
                '    ui: ui тесты',
                [f'    api_{_.name_snake}: api тесты {_.name_snake}' for _ in line["api"]],
                [f'    ui_{_["name"]}: ui тесты {_["name"]}' for _ in line["ui"]]
            ]
        wrapper()

    def set_readme(self):
        @self.creator(mode='creation', line=[Line(line='', path='README.md')])
        def wrapper(line):
            return [
                f'# Autotest (первый запуск, настройка для Windows)',
                f'- устанавливаем vscode',
                f'- устанавляваем python>=3.12',
                f'- клонируем репозиторий',
                f'- создаем витруальное окружение со всеми зависимостями',
                f'```',
                f'pip install --upgrade pip',
                f'cd {self.configuration.paths["path"].split("/")[-2]}',
                f'python -m venv .venv',
                r'.venv\Scripts\activate.ps1',
                f'pip install -r requirements.txt',
                ['$env:PLAYWRIGHT_DOWNLOAD_HOST="https://nexus-cache.services.mts.ru/repository/raw-playwright.azureedge.net-proxy"',
                '$env:NODE_TLS_REJECT_UNAUTHORIZED=0',
                'playwright install'] if self.configuration.ui == True else [],
                f'```',
                f'- открываем палитру команд (ctrl+shift+p)',
                f'- выбираем настройку тестов (configure tests)',
                f'- выбираем pytest',
                f'- выбираем {self.configuration.paths["path"].split("/")[-2]}',
                f'- запускаем тесты через вкладку тестирование',
                # '# Дополнительно (настройка .env)',
                # '- на основании шаблона .env.example создать файл .env',
                # '- заполнить данные о пользователях',
                # '    - admin - role_id (1,2,10,11,14,15,16,20,21,22,23)',
                # '    - regmn - role_id (3,4,5,6,7,11,17,18,19) region_id (02b50159-88e5-448c-935b-81f7cd8c0401, 087d56f0-fa0b-4dca-8163-f51880039387, 3ff456b7-98e3-4087-9fd9-9b60d3e40c0f, 46c2c07d-523d-430f-a6d9-6bd142858ad5, 5f476894-1f72-4940-8220-16b758167432, f58338d4-d8fe-4c75-9cfd-f12dc2725b63)',
                # '- данные о стенде получить из https://ocean.mts.ru/tenant/ac20b856-b7d9-49a1-a54d-178288f059b9/spaces/coffers-dev/iam/871a3c57-fa4b-43e5-bf7b-02b161738add?clientId=coffers-dev&stand=isso-dev.mts.ru'
            ]
        wrapper()

    def set_requirements(self):
        @self.creator(mode='creation', line=[Line(line='', path='requirements.txt')])
        def wrapper(line):
            return sorted([
                'pytest>=8.4.2',
                'pytest-playwright>=0.7.1',
                'pydantic>=2.12.3',
                'opencv-python>=4.12.0.88',
                'pytest-asyncio-cooperative>=0.40.0',
                'httpx>=0.28.1',
                'allure-pytest>=2.15.0',
                'python-dotenv>=1.2.1',
                'networkx>=3.6.1'
            ])
        wrapper()

    def set_gitignore(self):
        @self.creator(mode='creation', line=[Line(line='', path='.gitignore')])
        def wrapper(line):
            return sorted([
                f'{Path(__main__.__file__).name}',
                '.env',
                '.venv',
                '.pytest_cache',
                '__pycache__',
                'auth',
                'screenshots',
                'results',
                'videos'
            ])
        wrapper()

    def set_environments(self):
        @self.creator(mode='rewrite', line=[Line(line=_, path=_) for _ in [".env", ".env.example"]])
        def wrapper(line):
            return [
                [Text.to_comment_line(translation),
                sorted([f'{key.upper()}=\'{value if line == ".env" else ""}\'' for key, value in self.configuration.env.items() if section in key])] for section, translation in [("user", "ПОЛЬЗОВАТЕЛИ"), ("app", "СТЕНДЫ")]
            ]
        wrapper()

    def set_blank_client(self):
        @self.creator(mode='rewrite', line=[Line(line='', path=f'{self.configuration.paths["swagger"]}blank_client.py')])
        def wrapper(line):
            return [
                'import os',
                'from typing import Literal',
                'from httpx import AsyncClient',
                [f'from {self.configuration.paths["swagger_endpoints"].replace("/", ".")}{tag.name_snake} import {tag.name_camel}' for tag in self.configuration.tags],
                'class BlankClient:',
                '    TOKEN = {}',
                '    def __init__(self, client: AsyncClient):',
                '        self.__client = client',
                '    async def create_token(self, environment: dict):',
                '        data = {"grant_type": "password", "username": None, "password": None, "client_id": None, "client_secret": None}',
                '        for stand in environment:',
                '            users = environment[stand]["user"]',
                '            app = environment[stand]["app"]',
                '            for user in users:',
                '                data["username"] = os.environ[users[user]["login"]]',
                '                data["password"] = os.environ[users[user]["password"]]',
                '                data["client_id"] = os.environ[app["client_id"]]',
                '                data["client_secret"] = os.environ[app["client_secret"]]',
                '                response = await self.__client.post(os.environ[app["isso_url"]], data=data)',
                '                BlankClient.TOKEN.setdefault(stand, {}).setdefault(user, {}).setdefault("token", response.json()["access_token"])',
                '                BlankClient.TOKEN.setdefault(stand, {}).setdefault(user, {}).setdefault("domain", os.environ[app["domain"]])',
                f'    def set_token(self, client: Literal{list(self.configuration.environments[list(self.configuration.environments)[0]]["user"])} = "{list(self.configuration.environments[list(self.configuration.environments)[0]]["user"])[0]}", domain: Literal{list(self.configuration.environments)} = "{list(self.configuration.environments)[0]}"):',
                '        self.__client.base_url = BlankClient.TOKEN[domain][client]["domain"]',
                '        self.__client.headers = {"Authorization": f\'Bearer {BlankClient.TOKEN[domain][client]["token"]}\'}',
                '        self.__client.timeout = 20',
                [f'        self.{tag.name_snake.replace('_endpoint', '')} = {tag.name_camel}(self.__client)' for tag in self.configuration.tags]
            ]
        wrapper()

    def set_param_env(self):
        @self.creator(mode='rewrite', line=[Line(line='', path=f'{self.configuration.paths["params"]}param_env.py')])
        def wrapper(line):
            return [
                'import pytest',
                'from dataclasses import dataclass',
                '@dataclass',
                'class ParamEnv:',
                '    PARAM_USERS: tuple = (',
                '        "user",',
                '        [',
                [[
                '            pytest.param(',
                f'                "{user}",',
                f'                id="{user}",',
                f'            ),'] for user in self.configuration.environments[list(self.configuration.environments)[0]]["user"]],
                '        ]',
                '    )',
                '    PARAM_URLS: tuple = (',
                '        "url",',
                '        [',
                [['            pytest.param(',
                f'                "{url}",',
                f'                id="{url}",',
                '            ),'] for url in self.configuration.environments],
                '        ]',
                '    )',
            ]
        wrapper()

    def set_params_api(self):
        @self.creator(mode='addition', line=[Line(line=list(filter(lambda __: __.tags.name == _.name, self.configuration.endpoints)), path=f'{self.configuration.paths['params_api']}param_{_.name_snake}.py') for _ in self.configuration.tags])
        def wrapper(line: list[Endpoint]):
            return [
                'import pytest',
                'from dataclasses import dataclass',
                [['@dataclass',
                f'class Param{endpoint.names.name_camel}:',
                [[f'    PARAM_{method.name.upper()}_STATUS_{schema.status}: tuple = (',
                '        "param",',
                '        [',
                '            pytest.param(',
                '                {"sandbox": "sandbox"},',
                '                # marks=pytest.mark.skip(reason="sandbox"),',
                '                id="sandbox"',
                '            )',
                '        ]',
                '    )'] for method in endpoint.methods for schema in method.schemas if schema.status != None]] for endpoint in line]
            ]
        wrapper()

    # def set_tests_api(self):
    #     @self.creator(mode='addition', line=[Line(line=_, path=f'{self.configuration.paths["tests_test_api"]}test_{_.tags.name_snake}/test_{_.names.name_snake}.py') for _ in self.configuration.endpoints])
    #     def wrapper(line: Endpoint):
    #         return [
    #             'import pytest',
    #             f'from {self.configuration.paths["params"].replace("/", ".")}param_env import ParamEnv',
    #             f'from {self.configuration.paths["swagger"].replace("/", ".")}blank_client import BlankClient',
    #             f'from {self.configuration.paths["params_api"].replace("/", ".")}param_{line.tags.name_snake} import Param{line.names.name_camel}',
    #             [f'@pytest.mark.api_{line.tags.name_snake}',              
    #             '@pytest.mark.api',       
    #             '@pytest.mark.regression',
    #             f'class Test{line.names.name_camel}:',
    #             [[f'    @pytest.mark.asyncio_cooperative',
    #             f'    @pytest.mark.parametrize(*Param{line.names.name_camel}.PARAM_{method.name.upper()}_STATUS_{schema.status})',
    #             f'    @pytest.mark.parametrize(*ParamEnv.PARAM_USERS)',
    #             f'    async def test_{line.tags.name_snake}_{method.name}_status_{schema.status}(',
    #             f'        self,',
    #             f'        client: BlankClient,',
    #             f'        user,',
    #             f'        param',
    #             f'    ):',
    #             f'        client.set_token(client=user)',
    #             f'        pass'] for method in line.methods for schema in method.schemas if schema.status != None]]
    #         ]
    #     wrapper()

    def set_tests_api(self):
        # 4
        @self.creator(mode='addition', line=[Line(line=_, path=f'{self.configuration.paths["tests_test_api"]}test_{_.tags.name_snake}/test_{_.names.name_snake}.py') for _ in self.configuration.endpoints])
        def wrapper(line: Endpoint):
            return [
                'import pytest',
                f'from {self.configuration.paths["params"].replace("/", ".")}param_env import ParamEnv',
                f'from {self.configuration.paths["swagger"].replace("/", ".")}blank_client import BlankClient',
                f'from {self.configuration.paths["params_api"].replace("/", ".")}param_{line.tags.name_snake} import Param{line.names.name_camel}',
                [f'@pytest.mark.api_{line.tags.name_snake}',              
                '@pytest.mark.api',       
                '@pytest.mark.regression',
                # 1
                f'class Test{line.names.name_camel}:',
                [[f'    @pytest.mark.asyncio_cooperative',
                f'    @pytest.mark.parametrize(*Param{line.names.name_camel}.PARAM_{method.name.upper()}_STATUS_{schema.status})',
                f'    @pytest.mark.parametrize(*ParamEnv.PARAM_USERS)',
                # 2
                f'    async def test_{method.name}_{line.names.name_snake}_status_{schema.status}(',
                f'        self,',
                f'        client: BlankClient,',
                f'        user,',
                f'        param',
                f'    ):',
                f'        client.set_token(client=user)',
                f'        pass'] for method in line.methods for schema in method.schemas if schema.status != None]]
            ]
        wrapper()

    def set_pages(self):
        @self.creator(mode='addition', line=[Line(line={"page": _, "components": [___ for ___, count in Counter([__ for _ in self.configuration.pages for __ in _["components"]]).items() if count > 1]}, path=f'{self.configuration.paths["browser_pages"]}{_["name"]}.py') for _ in self.configuration.pages])
        def wrapper(line: dict[Literal["page", "components"], Page | str]):
            return [
                'from playwright.async_api import Page, expect',
                [f'from {self.configuration.paths["browser_components"].replace("/", ".")}component_{Text.to_snake_case(_)} import Component{Text.to_camel_case(_)}' for _ in line["page"]["components"] if _ in line["components"]],
                f'class {Text.to_camel_case(line["page"]["name"])}:',
                '    def __init__(self, page: Page):',
                [f'        self.{Text.to_snake_case(_.replace(f'{line["page"]["name"]}_', ''))} = {Text.to_camel_case(_.replace(f'{line["page"]["name"]}_', ''))}(page)' for _ in line["page"]["components"]],
                [[f'class {Text.to_camel_case(_)}(Component{Text.to_camel_case(_)}):' if _ in line["components"] else f'class {Text.to_camel_case(_.replace(f'{line["page"]["name"]}_', ''))}:',
                '    def __init__(self, page: Page):',
                '        super().__init__(page)' if _ in line["components"] else '        pass'] for _ in line["page"]["components"]]
            ]
        wrapper()

    def set_components(self):
        @self.creator(mode='addition', line=[Line(line=_, path=f'{self.configuration.paths['browser_components']}component_{_}.py') for _, count in Counter([__ for _ in self.configuration.pages for __ in _["components"]]).items() if count > 1])
        def wrapper(line):
            return [
                'from playwright.async_api import Page, expect',
                [f'class Component{Text.to_camel_case(line)}:',
                '    def __init__(self, page: Page):',
                '        pass']
            ]
        wrapper()

    def set_blank_page(self):
        @self.creator(mode='rewrite', line=[Line(line='', path=f'{self.configuration.paths['browser']}blank_page.py')])
        def wrapper(line):
            return [
                'from typing import Literal',
                'from playwright.async_api import Page',
                [f'from {self.configuration.paths["browser_pages"].replace("/", ".")}{Text.to_snake_case(_["name"])} import {Text.to_camel_case(_["name"])}' for _ in self.configuration.pages],
                'class BlankPage:',
                f'    URLS = Literal{sorted(list(set(_["url"] for _ in self.configuration.pages)))}',
                '    def __init__(self, page: Page):',
                '        self._page = page',
                '    async def close(self):',
                '        await self._page.close()',
                '    async def go_back(self):',
                '        await self._page.go_back()',
                '    async def reload(self):',
                '        await self._page.reload()',
                [f'    async def go_to(self, *, url: URLS = "", **kwargs):',
                '        for key, value in kwargs.items():',
                '            url = url.replace(f\'{{{key}}}\', str(value))',
                '        await self._page.goto(url=url, timeout=300000)',
                [f'        self.{Text.to_snake_case(_["name"]).replace('_page', '')} = {Text.to_camel_case(_["name"])}(self._page)' for _ in self.configuration.pages]]
            ]
        wrapper()

    def set_tests_ui(self):
        @self.creator(mode='addition', line=[Line(line={'page': page, 'component': _}, path=f'{self.configuration.paths["tests_test_ui"]}test_{page["name"]}/test_{Text.to_snake_case(page["name"] + '_' + _.replace(f'{page["name"]}_', ''))}.py') for page in self.configuration.pages for _ in page["components"]])
        def wrapper(line: dict[Literal["page", "component"], Page | str]):
            return [
                'import pytest',
                f'from {self.configuration.paths["params"].replace("/", ".")}param_env import ParamEnv',
                f'from {self.configuration.paths["browser"].replace("/", ".")}blank_page import BlankPage',
                f'from {self.configuration.paths["params_ui"].replace("/", ".")}param_{Text.to_snake_case(line["page"]["name"])} import Param{Text.to_camel_case(line["page"]["name"] + '_' + line['component'].replace(f'{line["page"]["name"]}_', ''))}',
                f'@pytest.mark.ui_{Text.to_snake_case(line["page"]["name"])}',              
                '@pytest.mark.ui',       
                '@pytest.mark.regression',
                f'class Test{Text.to_camel_case(line["page"]["name"] + '_' + line["component"].replace(f'{line["page"]["name"]}_', ''))}:',
                '    @pytest.mark.asyncio_cooperative',
                f'    @pytest.mark.parametrize(*Param{Text.to_camel_case(line["page"]["name"] + '_' + line["component"].replace(f'{line["page"]["name"]}_', ''))}.PARAM_{line["component"].replace(f'{line["page"]["name"]}_', '').upper()})',
                '    @pytest.mark.parametrize(*ParamEnv.PARAM_USERS)',
                f'    async def test_{Text.to_snake_case(line["page"]["name"] + '_' + line["component"])}(self, page: BlankPage, user, param):',
                f'        # await page.go_to(url={Text.to_snake_case(line["page"]["url"])})',
                '        pass'
            ]
        wrapper()

    def set_params_ui(self):
        @self.creator(mode='addition', line=[Line(line=_, path=f'{self.configuration.paths["params_ui"]}param_{_["name"]}.py') for _ in self.configuration.pages])
        def wrapper(line: Page):
            return [
                'import pytest',
                'from dataclasses import dataclass',
                [['@dataclass',
                f'class Param{Text.to_camel_case(line["name"] + '_' + _.replace(f'{line["name"]}_', ''))}:',
                f'    PARAM_{_.replace(f'{line["name"]}_', '').upper()}: tuple = (',
                '        "param",',
                '        [',
                '            pytest.param(',
                '                {"sandbox": "sandbox"},',
                '                # marks=pytest.mark.skip(reason="sandbox"),',
                '                id="sandbox"',
                '            )',
                '        ]',
                '    )'] for _ in line["components"]]
            ]
        wrapper()


class FastTest:

    def __init__(self):
        self.configuration = Configuration()
        self.creator = Creator
        self.create = Create(self.configuration)

    def create_api_tests(self):
        self.create.set_gitignore()
        self.create.set_requirements()
        self.create.set_readme()
        self.create.set_environments()
        self.create.set_pytest()
        self.create.set_param_env()
        self.create.set_blank_client()
        self.create.set_conftest_api()
        self.create.set_params_api()
        self.create.set_endpoints()
        self.create.set_schemas()
        self.create.set_tests_api()

    def create_ui_tests(self):
        self.create_api_tests()
        self.create.set_blank_page()
        self.create.set_params_ui()
        self.create.set_components()
        self.create.set_pages()
        self.create.set_conftest_ui()
