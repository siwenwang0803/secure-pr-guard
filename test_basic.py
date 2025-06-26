try:
    from graph_review import create_review_graph
    print("✅ Import successful")
    
    raw_graph, workflow = create_review_graph()
    print("✅ Graph creation successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
