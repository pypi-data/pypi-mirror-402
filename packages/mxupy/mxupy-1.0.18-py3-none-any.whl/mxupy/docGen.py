import os
import ast

module_dir = os.path.dirname(__file__)


def extract_comments_from_file(file_path):
    '''
    获取模块文件的注释
    Args:
        file_path (str): 模块文件路径

    Returns:
        str: 注释文本（markdown格式）
    '''
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read())
        comments = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                comments.append(f"### {node.name}\n\n{docstring}\n")
        return comments


def generate_markdown_docstring(title, dir_path, output_file):
    '''
    生成 docstring markdown 文档。
    Args:
        title (str): 标题
        dir_path (str): 包目录
        output_file (str): md 文件路径
    '''

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# {title}\n\n---\n\n")
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = os.path.join(root, file_name)
                    comments = extract_comments_from_file(file_path)
                    if comments:
                        md_file.write(f"## {file_name}\n\n---\n\n")
                        md_file.writelines(comments)


if __name__ == "__main__":

    # 示例用法
    generate_markdown_docstring('mxupy 编程参考', os.path.join(module_dir, './mxupy'), os.path.join(module_dir, './docs/README.md'))
