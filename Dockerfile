FROM base_mirror:1.0.0

#复制代码文件到容器
COPY .  /home/fastapi-blog

#设置工作目录
WORKDIR /home/fastapi-blog

# 安装项目依赖文件到容器
RUN pip install -r /home/fastapi-blog/requirements.txt -i https://pypi.douban.com/simple

CMD ["uvicorn", "diagnose.app.main:app", "--host", "0.0.0.0", "--port", "8090"]