import sys
import uuid
from src.graph import build_graph


def main():
    if len(sys.argv) < 2:
        print('Usage: python src/main.py "your research question"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    session_id = str(uuid.uuid4())

    app = build_graph()
    final_state = app.invoke({"topic": topic, "session_id": session_id})

    print("\n" + "=" * 60)
    print("DEBATE TRACE")
    print("=" * 60)
    for step in final_state["trace"]:
        print(f"\n[{step['agent']}] {step['action']}")

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(final_state["report"])


if __name__ == "__main__":
    main()
