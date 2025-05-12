import sys
from src.graph import build_graph

def main():
    if len(sys.argv) < 2:
        print("Use: python run.py \"ask your question\"")
        sys.exit(1)

    raw_query = sys.argv[1]
    print(f"\n Raw query: {raw_query}\n")

    agent = build_graph()

    # Ejecutar el agente con la consulta
    final_state = agent.invoke({"raw_query": raw_query})

    print("\n Execution completed.")
    if 'result' in final_state:
        print("\n Final result:")
        print(final_state['result'])

if __name__ == "__main__":
    main()
