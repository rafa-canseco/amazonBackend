import json

import openai


class AIClass:
    def __init__(self, api_key: str, model: str):
        if not api_key or len(api_key) == 0:
            raise ValueError("OPENAI_KEY is missing")

        self.openai = openai
        self.openai.api_key = api_key
        self.model = model

    async def normalize_category_fn(
        self, category: str, model: str = None, temperature: float = 0
    ) -> dict:
        try:
            response = self.openai.chat.completions.create(
                model=model or self.model,
                temperature=temperature,
                messages=[{"role": "user", "content": category}],
                functions=[
                    {
                        "name": "fn_get_prediction_category",
                        "description": "Predict the correct category given the input text in Spanish or English. "
                        "Map to standard shipping categories.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prediction": {
                                    "type": "string",
                                    "description": "The predicted product category.",
                                    "enum": [
                                        "Books",
                                        "CDs, Cassettes, Vinyl",
                                        "VHS Videotapes",
                                        "DVDs and Blu-ray",
                                        "Video Games",
                                        "Software & Computer Games",
                                        "Camera & Photo",
                                        "Tools & Hardware",
                                        "Kitchen & Housewares",
                                        "Computer",
                                        "Outdoor Living",
                                        "Electronics",
                                        "Sports & Outdoors",
                                        "Cell Phones & Service",
                                        "Musical Instruments",
                                        "Office Products",
                                        "Toy & Baby",
                                        "Independent Design items",
                                        "Everything Else",
                                    ],
                                }
                            },
                            "required": ["prediction"],
                        },
                    }
                ],
                function_call={"name": "fn_get_prediction_category"},
            )
            function_call = response.choices[0].message.function_call
            arguments = function_call.arguments
            prediction = json.loads(arguments)
            print(prediction)
            return prediction
        except Exception as e:
            print(e)
            return {"prediction": ""}

    async def extract_weight_fn(
        self, specifications: list, model: str = None, temperature: float = 0
    ) -> dict:
        try:
            response = self.openai.chat.completions.create(
                model=model or self.model,
                temperature=temperature,
                messages=[{"role": "user", "content": str(specifications)}],
                functions=[
                    {
                        "name": "fn_extract_weight",
                        "description": (
                            "Extract weight value and unit from product dimensions if present"
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "weight_value": {
                                    "type": "string",
                                    "description": (
                                        "The numeric weight value extracted, or 'no_weight' if not found"
                                    ),
                                },
                                "weight_unit": {
                                    "type": "string",
                                    "description": (
                                        "The weight unit (g, kg, lb, oz) or 'no_unit' if not found"
                                    ),
                                    "enum": ["g", "kg", "lb", "oz", "no_unit"],
                                },
                            },
                            "required": ["weight_value", "weight_unit"],
                        },
                    }
                ],
                function_call={"name": "fn_extract_weight"},
            )

            function_call = response.choices[0].message.function_call
            arguments = function_call.arguments
            prediction = json.loads(arguments)
            print(prediction)
            return prediction
        except Exception as e:
            print(e)
            return {"weight_value": "no_weight", "weight_unit": "no_unit"}
