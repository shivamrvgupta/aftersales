import os
from together import Together

# Initialize the Together client with your API key
client = Together(api_key="0cbd0ea0ab56786ea56c58276856f499ae34620580e94d77344fe1bf0ba149e2")

class AIService:
    """
    A class providing AI-powered services.
    """

    @staticmethod
    def estimate_cost(fault_description: str) -> dict:
        """
        Estimates the repair cost for a given fault description.

        Args:
        fault_description (str): A detailed description of the fault.

        Returns:
        dict: A dictionary containing the estimated cost or an error message.
        """

        try:
            # Create a completion request to the Meta-Llama model
            response_generator = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                messages=[
                    {
                        "role": "user",
                        "content": f"Estimate the repair cost for the following fault description in INR only: {fault_description}. Please provide just the costs (e.g., '1000 INR, 5000 INR')."
                    }
                ],
                max_tokens=1024,
                temperature=0.0,  # Lower temperature for more deterministic responses
                top_p=1.0,        # Use all probabilities
                top_k=0,          # Do not limit the number of top tokens
                repetition_penalty=1,
                stop=["\n", "\n\n"],
                stream=True
            )

            # Initialize an empty string to store the response text
            response_text = ""

            # Iterate over the response generator to collect the response chunks
            for chunk in response_generator:
                # Extract only the content of each chunk
                content = chunk.choices[0].delta.content  # Accessing just the text content
                if content:
                    response_text += content

            # Return the estimated cost as a dictionary
            return {"estimated_cost": response_text.strip(), "message": "Repair cost estimated successfully", "status": True, "status_code": 200}

        except Exception as e:
            # Return an error message if an exception occurs
            return {"error": str(e), "message": "Failed to estimate repair cost", "status": False, "status_code": 500}
