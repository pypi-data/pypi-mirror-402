import os


def zipFolder(folder_path, output_path, exclude_dirs=None):
    """
    压缩文件夹并排除指定的目录。

    :param folder_path: 要压缩的文件夹的路径。
    :param output_path: 压缩文件的输出路径。
    :param exclude_dirs: 要排除的目录列表。
    """
    import zipfile
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            # 排除指定目录
            if exclude_dirs is not None:
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                # 添加文件到压缩包
                zipf.write(file_path, os.path.relpath(file_path, folder_path))


def addFolderToZip(zip_file_path, folder_path):
    '''
    添加文件夹到zip文件
    '''
    import zipfile

    rdir = folder_path[0:folder_path.rstrip('\\').rfind('\\')].rstrip('\\') + '\\'

    # 以追加模式打开已存在的zip文件
    with zipfile.ZipFile(zip_file_path, "a") as zipf:
        # 遍历文件夹中的所有文件和子文件夹
        for root, dirs, files in os.walk(folder_path):
            # 遍历所有文件，并添加到zip文件中，并保持相对路径
            for file in files:
                fn = os.path.join(root, file)
                rfn = os.path.relpath(fn, rdir)
                zipf.write(fn, rfn)

        # 关闭zip文件
        zipf.close()
