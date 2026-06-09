from backend.app.core.schemas import EventCreate
from backend.app.services.pipeline import MemoryPipeline


DEMO_EVENTS = [
    "今天继续研究 ESP32 的语音采集方案，感觉 VAD 要先在手机端做，避免服务器存太多无意义音频。",
    "Allen Memory OS 的核心不是保存所有录音，而是自动提炼长期有价值的记忆。",
    "转学申请需要整理 History 和 Math 的材料，下周要列一个 checklist。",
    "我希望这个项目保持 vibe coding 的感觉，先做能用的开源 MVP，再慢慢变强。",
    "关于 NAS 的方案，我倾向先用现有硬件验证数据同步，不急着买新设备。",
]


def main() -> None:
    pipeline = MemoryPipeline()
    for text in DEMO_EVENTS:
        row = pipeline.ingest_event(EventCreate(text=text, source="demo"))
        print(f"#{row['id']} [{row['category']}] importance={row['importance']}: {row['text']}")


if __name__ == "__main__":
    main()

