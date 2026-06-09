from datetime import date

from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine


def main() -> None:
    today = date.today()
    pipeline = MemoryPipeline()
    summary = pipeline.summarize_day(today)
    reflection = ReflectionEngine(pipeline.store).reflect_on_day(today)

    print(f"Summary saved for {summary['day']}")
    print(summary["summary"])
    print()
    print(f"Reflection saved for {reflection['day']}")
    print(reflection["text"])


if __name__ == "__main__":
    main()

