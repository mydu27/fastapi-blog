FROM base_mirror:1.0.0

#复制代码文件到容器
COPY .  /home/fastapi-blog

#设置工作目录
WORKDIR /home/fastapi-blog

# 安装项目依赖文件到容器
RUN pip install -r /home/fastapi-blog/requirements.txt -i https://pypi.douban.com/simple

CMD ["gunicorn", "app.main:app", "–preload", "-w", "4", "-b", "0.0.0.0:8090", "-k", "uvicorn.workers.UvicornWorker"]