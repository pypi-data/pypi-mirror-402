import typer
import json
import logging
from pathlib import Path
from pydantic import TypeAdapter
from factory import downloader_factory, email_factory, provider_factory
from data.bill_profile import PayConfig
from typing_extensions import Annotated
from cli.root import app


def run(provider: str):
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    config_path = Path.home() / ".flow" / "config.json"
    
    logging.info(f"开始下载 {provider} 账单...")
    logging.info(f"配置文件路径: {config_path}")

    try:
        # 使用 ConfigLoader 加载配置（支持环境变量替换）
        from config.loader import load_config 
        config_json = load_config(config_path)
        
        logging.info(f"配置加载成功")
        
        adapter = TypeAdapter(PayConfig)
        config_obj = adapter.validate_python(config_json[provider])
        downloader = downloader_factory.creat_downloader(config_obj.download)
        email = email_factory.create_emial(
            config_obj.email, config_obj.auth.model_dump(), config_obj.auth_type.value
        )

        provider_obj = provider_factory.create_workder(provider)
        provider_obj.email = email
        provider_obj.downloader = downloader
        provider_obj.bill = config_obj.profile

        logging.info(f"开始执行下载...")
        provider_obj.process_bills()
        logging.info(f"✅ 下载完成！")

    except FileNotFoundError as e:
        logging.error(f"配置文件未找到: {config_path}")
        raise
    except KeyError as e:
        logging.error(f"配置中缺少 provider: {provider}")
        raise
    except Exception as e:
        logging.error(f"处理失败: {e}")
        raise


@app.command()
def download(
    provider: Annotated[
        str, typer.Option("--provider", "-p", help="config file")
    ] = "alipay",
):
    run(provider)
