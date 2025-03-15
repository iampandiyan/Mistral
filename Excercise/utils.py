import os
import json
import openai
import re
from collections import defaultdict
from mistralai import Mistral

products_file = 'products.json'
categories_file = 'categories.json'
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"
client = Mistral(api_key=api_key)

delimiter = "####"
step_2_system_message_content = f"""
You will be provided with customer service a conversation. \
The most recent user query will be delimited with \
{delimiter} characters.
Output a python list of objects, where each object has \
the following format:
    'category': <one of Computers and Laptops, \
    Smartphones and Accessories, \
    Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, 
    Audio Equipment, Cameras and Camcorders>,
OR
    'products': <a list of products that must \
    be found in the allowed products below>

Where the categories and products must be found in \
the customer service query.
If a product is mentioned, it must be associated with \
the correct category in the allowed products list below.
If no products or categories are found, output an \
empty list.
Only list products and categories that have not already \
been mentioned and discussed in the earlier parts of \
the conversation.

Allowed products: 

Computers and Laptops category:
TechPro Ultrabook
BlueWave Gaming Laptop
PowerLite Convertible
TechPro Desktop
BlueWave Chromebook

Smartphones and Accessories category:
SmartX ProPhone
MobiTech PowerCase
SmartX MiniPhone
MobiTech Wireless Charger
SmartX EarBuds

Televisions and Home Theater Systems category:
CineView 4K TV
SoundMax Home Theater
CineView 8K TV
SoundMax Soundbar
CineView OLED TV

Gaming Consoles and Accessories category:
GameSphere X
ProGamer Controller
GameSphere Y
ProGamer Racing Wheel
GameSphere VR Headset

Audio Equipment category:
AudioPhonic Noise-Canceling Headphones
WaveSound Bluetooth Speaker
AudioPhonic True Wireless Earbuds
WaveSound Soundbar
AudioPhonic Turntable

Cameras and Camcorders category:
FotoSnap DSLR Camera
ActionCam 4K
FotoSnap Mirrorless Camera
ZoomMaster Camcorder
FotoSnap Instant Camera

Only output the list of objects, with nothing else.
"""

step_2_system_message = {'role':'system', 'content': step_2_system_message_content}    


step_4_system_message_content = f"""
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with VERY concise answers. \
    Make sure to ask the user relevant follow-up questions.
"""

step_4_system_message = {'role':'system', 'content': step_4_system_message_content}    

step_6_system_message_content = f"""
    You are an assistant that evaluates whether \
    customer service agent responses sufficiently \
    answer customer questions, and also validates that \
    all the facts the assistant cites from the product \
    information are correct.
    The conversation history, product information, user and customer \
    service agent messages will be delimited by \
    3 backticks, i.e. ```.
    Respond with a Y or N character, with no punctuation:
    Y - if the output sufficiently answers the question \
    AND the response correctly uses product information
    N - otherwise

    Output a single letter only.
"""

step_6_system_message = {'role':'system', 'content': step_6_system_message_content}    


def get_completion_from_messages(messages, 
                                 model=model, 
                                 temperature=0, max_tokens=500):
    response = client.chat.complete(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens, 
    )
    return response.choices[0].message.content

def create_categories():
    categories_dict = {
      'Billing': [
                'Unsubscribe or upgrade',
                'Add a payment method',
                'Explanation for charge',
                'Dispute a charge'],
      'Technical Support':[
                'General troubleshooting'
                'Device compatibility',
                'Software updates'],
      'Account Management':[
                'Password reset'
                'Update personal information',
                'Close account',
                'Account security'],
      'General Inquiry':[
                'Product information'
                'Pricing',
                'Feedback',
                'Speak to a human']
    }
    
    with open(categories_file, 'w') as file:
        json.dump(categories_dict, file)
        
    return categories_dict


def get_categories():
    with open(categories_file, 'r') as file:
            categories = json.load(file)
    return categories


def get_product_list():
    """
    Used in L4 to get a flat list of products
    """
    products = get_products()
    product_list = []
    for product in products.keys():
        product_list.append(product)
    
    return product_list

def get_products_and_category():
    """
    Used in L5
    """
    products = get_products()
    products_by_category = defaultdict(list)
    for product_name, product_info in products.items():
        category = product_info.get('category')
        if category:
            products_by_category[category].append(product_info.get('name'))
    
    return dict(products_by_category)

def get_products():
    with open(products_file, 'r') as file:
        products = json.load(file)
    return products

def find_category_and_product(user_input,products_and_category):
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, Audio Equipment, Cameras and Camcorders>,
    OR
        'products': <a list of products that must be found in the allowed products below>

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category in the allowed products list below.
    If no products or categories are found, output an empty list.

    The allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}
    
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_completion_from_messages(messages)

def find_category_and_product_only(user_input,products_and_category):
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of objects, where each object has the following format:
    'category': <one of Computers and Laptops, Smartphones and Accessories, Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, Audio Equipment, Cameras and Camcorders>,
    OR
    'products': <a list of products that must be found in the allowed products below>

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category in the allowed products list below.
    If no products or categories are found, output an empty list.

    Allowed products: 
    Computers and Laptops category:
TechPro Ultrabook
BlueWave Gaming Laptop
PowerLite Convertible
TechPro Desktop
BlueWave Chromebook

Smartphones and Accessories category:
SmartX ProPhone
MobiTech PowerCase
SmartX MiniPhone
MobiTech Wireless Charger
SmartX EarBuds

Televisions and Home Theater Systems category:
CineView 4K TV
SoundMax Home Theater
CineView 8K TV
SoundMax Soundbar
CineView OLED TV

Gaming Consoles and Accessories category:
GameSphere X
ProGamer Controller
GameSphere Y
ProGamer Racing Wheel
GameSphere VR Headset

Audio Equipment category:
AudioPhonic Noise-Canceling Headphones
WaveSound Bluetooth Speaker
AudioPhonic True Wireless Earbuds
WaveSound Soundbar
AudioPhonic Turntable

Cameras and Camcorders category:
FotoSnap DSLR Camera
ActionCam 4K
FotoSnap Mirrorless Camera
ZoomMaster Camcorder
FotoSnap Instant Camera
    
    Only output the list of objects, nothing else.
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_completion_from_messages(messages)

def get_products_from_query(user_msg):
    """
    Code from L5, used in L8
    """
    products_and_category = get_products_and_category()
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, Audio Equipment, Cameras and Camcorders>,
    OR
        'products': <a list of products that must be found in the allowed products below>

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category in the allowed products list below.
    If no products or categories are found, output an empty list.

    The allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}

    """
    
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    ] 
    category_and_product_response = get_completion_from_messages(messages)
    
    return category_and_product_response


# product look up (either by category or by product within category)
def get_product_by_name(name):
    products = get_products()
    return products.get(name, None)

def get_products_by_category(category):
    products = get_products()
    return [product for product in products.values() if product["category"] == category]

def get_mentioned_product_info(data_list):
    """
    Used in L5 and L6
    """
    product_info_l = []

    if data_list is None:
        return product_info_l

    for data in data_list:
        try:
            if "products" in data:
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        product_info_l.append(product)
                    else:
                        print(f"Error: Product '{product_name}' not found")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    product_info_l.append(product)
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return product_info_l



def read_string_to_list(input_string):
    """
    Converts a string (possibly copy-pasted with code block markers) to a list.
    Replaces single quotes and strips formatting markers like ```python.
    """
    if not input_string or input_string.strip().lower() in ['none', 'null', '']:
        print("Warning: Input is empty or null-like.")
        return None

    try:
        print("Original input:", input_string)

        # Remove markdown-style code block markers (``` or ```python)
        cleaned_input = re.sub(r"```(?:python)?", "", input_string).strip()

        # Replace single quotes with double quotes for valid JSON
        cleaned_input = cleaned_input.replace("'", '"')

        print("Cleaned input:", cleaned_input)

        return json.loads(cleaned_input)

    except json.JSONDecodeError as e:
        print("Error: Invalid JSON string:", e)
        return None

def generate_output_string(data_list):
    output_string = ""

    if data_list is None:
        return output_string

    for data in data_list:
        try:
            if "products" in data:
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        output_string += json.dumps(product, indent=4) + "\n"
                    else:
                        print(f"Error: Product '{product_name}' not found")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    output_string += json.dumps(product, indent=4) + "\n"
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return output_string

# Example usage:
#product_information_for_user_message_1 = generate_output_string(category_and_product_list)
#print(product_information_for_user_message_1)

def answer_user_msg(user_msg,product_info):
    """
    Code from L5, used in L6
    """
    delimiter = "####"
    system_message = f"""
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with concise answers. \
    Make sure to ask the user relevant follow up questions.
    """
    # user_msg = f"""
    # tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also what tell me about your tvs"""
    messages =  [  
    {'role':'system', 'content': system_message},  
    {'role':'assistant', 'content': f"Relevant product information:\n{product_info}"},
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},
    ] 
    response = get_completion_from_messages(messages)
    return response

def create_products():
    """
        Create products dictionary and save it to a file named products.json
    """
    # product information
    # fun fact: all these products are fake and were generated by a language model
    products = {        
        "FotoSnap Mirrorless Camera": {
            "name": "FotoSnap Mirrorless Camera",
            "category": "Cameras and Camcorders",
            "brand": "FotoSnap",
            "model_number": "FS-ML100",
            "warranty": "1 year",
            "rating": 4.6,
            "features": ["20.1MP sensor", "4K video", "3-inch touchscreen", "Interchangeable lenses"],
            "description": "A compact and lightweight mirrorless camera with advanced features.",
            "price": 799.99
        },
        "ZoomMaster Camcorder": {
            "name": "ZoomMaster Camcorder",
            "category": "Cameras and Camcorders",
            "brand": "ZoomMaster",
            "model_number": "ZM-CM50",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["1080p video", "30x optical zoom", "3-inch LCD", "Image stabilization"],
            "description": "Capture life's moments with this easy-to-use camcorder.",
            "price": 249.99
        },
        "FotoSnap Instant Camera": {
            "name": "FotoSnap Instant Camera",
            "category": "Cameras and Camcorders",
            "brand": "FotoSnap",
            "model_number": "FS-IC10",
            "warranty": "1 year",
            "rating": 4.1,
            "features": ["Instant prints", "Built-in flash", "Selfie mirror", "Battery-powered"],
            "description": "Create instant memories with this fun and portable instant camera.",
            "price": 69.99
        }
    }

    products_file = 'products.json'
    with open(products_file, 'w') as file:
        json.dump(products, file)
        
    return products