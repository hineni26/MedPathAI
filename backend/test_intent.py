# test_graph.py
import asyncio
from graph import run_graph

async def test():
    # Test 1 — direct procedure
    print("=== TEST 1: Direct procedure ===")
    result = await run_graph(
        user_input    = "I need knee replacement in Pune, budget 2 lakh",
        user_profile  = {
            "name": "Rahul", "age": 45, "city": "Pune",
            "comorbidities": ["hypertension"],
            "insurance_provider": "HDFC Ergo",
            "insurance_coverage": 100000,
        },
        user_financials = {
            "monthly_income": 42000,
            "existing_emi": 8200,
            "cibil_score": 742,
            "employment_years": 4,
        }
    )
    print("Explanation:", result.get("explanation"))
    print("Hospitals:", len(result.get("hospitals", [])))
    print("Graph path:", result.get("graph_path"))
    print()

    # Test 2 — emergency
    print("=== TEST 2: Emergency ===")
    result2 = await run_graph(
        user_input   = "I have chest pain spreading to my left arm",
        user_profile = {
            "name": "Rahul", "age": 45, "city": "Nagpur",
            "comorbidities": ["hypertension"],
        }
    )
    print("Emergency:", result2.get("is_emergency"))
    print("Graph path:", result2.get("graph_path"))

asyncio.run(test())