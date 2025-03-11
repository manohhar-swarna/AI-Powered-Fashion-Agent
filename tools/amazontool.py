from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel,Field
import re
import http.client
from itertools import product
import json
import random
from dotenv import load_dotenv
import os
from openai import OpenAI


class AmazonShoppingInput(BaseModel):
    """Input schema for MyCustomTool."""
    top_list: list = Field(..., description="list of top names from the 3 outfit sets")
    bottom_list: list = Field(..., description="list of bottom names from the 3 outfit sets")
    footwear_list: list = Field(..., description="list of footwear names from the 3 outfit sets")
    accessories_list: list = Field(..., description="list of accessories names from the 3 outfit sets")
    outfit_set_summary: list = Field(..., description="list of outfit summary from the 3 outfit sets")
    user_budget: int = Field(..., description="User provided budget value for the outfit.")

class AmazonShoppingTool(BaseTool):
    name: str = "Amazon_Shopping_tool"
    description: str = """This tool do the shopping for the outfit sets provided by the Outfit designer 
    expert."""
    args_schema: Type[BaseModel] = AmazonShoppingInput
    serper_api_key: Optional[str] = None
    client: Optional[str] = None

    def __init__(self):

        super().__init__()  # Call the parent class's __init__ if necessary
        load_dotenv()
        self.client = OpenAI()
        self.serper_api_key = os.environ.get('SERPER_API_KEY')

    def serper_search(self,query):
        amazon_products_list=[]
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({
        "q": f"{query} in amazon.com"
        })
        headers = {
        'X-API-KEY':"8569804111bc9d79ca2f0319b0e8c83fad1e4e1c",
        'Content-Type': 'application/json'
        }
        conn.request("POST", "/shopping", payload, headers)
        res = conn.getresponse()
        data = res.read()
        # show me the result in json format
        result_json = json.loads(data.decode("utf-8"))
        for product_dict in result_json['shopping']:    
            if "Amazon.com" in product_dict["source"]:
                amazon_products_list.append(product_dict)
        return amazon_products_list
    
    def get_number(self,s):

        numeric_value = re.findall(r'\d+\.\d+|\d+', s)
        numeric_value = float(numeric_value[0]) if numeric_value else None
        return numeric_value
    
    def get_budget_based_outfits(self,amazon_top_products_list,amazon_bottom_products_list,
                                 amazon_footwear_products_list,amazon_accessories_products_list,user_budget):
        
        budget_outfit_list=[]
        non_budget_outfit_list=[]
        for top, bottom, footwear,accessories in product(amazon_top_products_list,
                                                        amazon_bottom_products_list,
                                                        amazon_footwear_products_list,
                                                        amazon_accessories_products_list):
            
            outfit_price = self.get_number(top["price"])+self.get_number(bottom["price"])+self.get_number(footwear["price"])+self.get_number(accessories["price"])
            if outfit_price <= user_budget:
                
                budget_outfit_list.append(
                {"outfit_set":{
                    "top": {"name":top["title"],"product_url":top["link"],"price":top["price"],
                            "image_url":top["imageUrl"]},
                    "bottom": {"name":bottom["title"],"product_url":bottom["link"],"price":bottom["price"],
                            "image_url":bottom["imageUrl"]},
                    "footwear": {"name":footwear["title"],"product_url":footwear["link"],
                                 "price":footwear["price"],"image_url":footwear["imageUrl"]},
                    "accessories": {"name":accessories["title"],"product_url":accessories["link"],
                                 "price":accessories["price"],"image_url":accessories["imageUrl"]},
                    "outfit_set_price":str(round(outfit_price))+'$'}})
            else:
                non_budget_outfit_list.append({"outfit_set":{
                    "top": {"name":top["title"],"product_url":top["link"],"price":top["price"],
                            "image_url":top["imageUrl"]},
                    "bottom": {"name":bottom["title"],"product_url":bottom["link"],"price":bottom["price"],
                            "image_url":bottom["imageUrl"]},
                    "footwear": {"name":footwear["title"],"product_url":footwear["link"],
                                 "price":footwear["price"],"image_url":footwear["imageUrl"]},
                    "accessories": {"name":accessories["title"],"product_url":accessories["link"],
                                 "price":accessories["price"],"image_url":accessories["imageUrl"]},
                    "outfit_set_price":str(round(outfit_price))+'$'}})
                
        if budget_outfit_list:
            budget_pointer=1
            return budget_outfit_list,budget_pointer
        else:
            budget_pointer=0
            return non_budget_outfit_list,budget_pointer
        
    def prepare_product_type_items(self,budget_outfit_list,product_type):
            
            items_dict={}
            for outfit in budget_outfit_list:
                  if(outfit["outfit_set"][product_type]["name"] not in items_dict):
                        items_dict[outfit["outfit_set"][product_type]["name"]]=outfit["outfit_set"][product_type]["image_url"]

            return items_dict

    def get_best_fashion_item(self,product_type_items,outfit_set_summary):

        content_list=[]
        user_text="""Please find the below provided images and 
                    outfit summary. Select the best product image.
                    The output must be in below format i,e
                    Name : provided name of the selected product image
                    Reason : Brief describe why this selectd product image is best match for the provided outfit summary
                    Ensure the output is a valid JSON string.
                    outfit summary:
                    {}
                    """
        content_list.append({"type":"text","text":user_text.format(outfit_set_summary)})
        for product_name,image_url in product_type_items.items():
            content_list.append({"type": "text", "text": f"{product_name}:"})
            content_list.append({"type":"image_url","image_url":{"url":f"{image_url}"}})

        response = self.client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": """You are fashion expert with huge knowledge on outfit designs and
             excellent taste of fashion. Your key skill is, by considering the provided outfit summary,
             performing in-dept analysis on provided prodcut images, and selecting the best product image 
             out of the provided product images."""},
            {"role": "user", "content":content_list}
        ])
        
        result=response.choices[0].message.content.replace('json','')
        result=result.replace("```","")
        result=json.loads(result)
        return result
    
    def search_outfit_list(self,budget_outfit_list,best_fashion_top,product_type):
        item_dict=None
        reason=None
        for outfit in budget_outfit_list:
            if(best_fashion_top['Name']==outfit['outfit_set'][product_type]['name']):
                item_dict=outfit['outfit_set'][product_type]
                reason=best_fashion_top['Reason']
                break
        return item_dict,reason

        
    def get_final_fashion_outfit(self,budget_outfit_list,best_fashion_top,best_fashion_bottom,
                                     best_fashion_footwear,best_fashion_accessories,outfit_type):
        
        final_top_for_outfit,top_reason=self.search_outfit_list(budget_outfit_list,best_fashion_top,"top")
        final_bottom_for_outfit,bottom_reason=self.search_outfit_list(budget_outfit_list,
                                              best_fashion_bottom,"bottom")
        final_footwear_for_outfit,footwear_reason=self.search_outfit_list(budget_outfit_list,
                                                  best_fashion_footwear,"footwear")
        final_accessories_for_outfit,accessories_reason=self.search_outfit_list(budget_outfit_list,
                                                        best_fashion_accessories,"accessories")
        final_outfit_price=self.get_number(final_top_for_outfit['price'])+self.get_number(final_bottom_for_outfit['price'])+self.get_number(final_footwear_for_outfit['price'])+self.get_number(final_accessories_for_outfit['price'])
        
        output_string="""
        {} :
        
        Top : {}
        Top price :{}
        Reason for this Top : {}
        Top pruchase link : {}
        Top image url : {}

        Bottom : {}
        Bottom price :{}
        Reason for this Bottom : {}
        Bottom pruchase link : {}
        Bottom image url : {}
        
        Footwear : {}
        Footwear price :{}
        Reason for this Footwear : {}
        Footwear pruchase link : {}
        Footwear image url : {}

        Accessories : {}
        Accessories price :{}
        Reason for this Accessories : {}
        Accessories pruchase link : {}
        Accessories image url : {}
    
        Outfit Total Price : {}
        """
        output_string=output_string.format(outfit_type,final_top_for_outfit['name'],final_top_for_outfit['price'],
                                           top_reason,final_top_for_outfit['product_url'],
                                           final_top_for_outfit['image_url'],final_bottom_for_outfit['name'],
                                           final_bottom_for_outfit['price'],bottom_reason,final_bottom_for_outfit['product_url'],
                                           final_bottom_for_outfit['image_url'],final_footwear_for_outfit['name'],
                                           final_footwear_for_outfit['price'],footwear_reason,final_footwear_for_outfit['product_url'],
                                           final_footwear_for_outfit['image_url'],final_accessories_for_outfit['name'],
                                           final_accessories_for_outfit['price'],accessories_reason,final_accessories_for_outfit['product_url'],
                                           final_accessories_for_outfit['image_url'],str(round(final_outfit_price))+"$")
      
        return output_string


    def shop_items(self,top_name,bottom_name,footwear_name,accessories_name,outfit_set_summary,user_budget):

        output_string="""
        Budget based outfit :
        
        Top : {}
        Top price :{}
        Top pruchase link : {}
        Top image url : {}

        Bottom : {}
        Bottom price :{}
        Bottom pruchase link : {}
        Bottom image url : {}
        
        Footwear : {}
        Footwear price :{}
        Footwear pruchase link : {}
        Footwear image url : {}

        Accessories : {}
        Accessories price :{}
        Accessories pruchase link : {}
        Accessories image url : {}
    
        Outfit Total Price : {}
        """

        print("searching items with serper search...")

        amazon_top_products_list=self.serper_search(top_name)
        amazon_bottom_products_list=self.serper_search(bottom_name)
        amazon_footwear_products_list=self.serper_search(footwear_name)
        amazon_accessories_products_list=self.serper_search(accessories_name)

        print("Items search completed, gathered all amazon products...")
        
        print("Starting the process of creating outfit sets based on the user budget...")

        budget_outfit_list,budget_pointer=self.get_budget_based_outfits(amazon_top_products_list,amazon_bottom_products_list,
                                 amazon_footwear_products_list,amazon_accessories_products_list,user_budget)
        
        print(f"""Sample outfit set : 
              {budget_outfit_list[0]}""")
        print("Successfully created the outfit sets based on the budget...")
        
        if(len(budget_outfit_list)!=1 and budget_pointer==1):

            print("Starting the process of creating fashion based outfit with vision model...")
            print("Preparing the data for vision model...")

            top_items_dict=self.prepare_product_type_items(budget_outfit_list,"top")
            bottom_items_dict=self.prepare_product_type_items(budget_outfit_list,"bottom")
            footwear_items_dict=self.prepare_product_type_items(budget_outfit_list,"footwear")
            accessories_items_dict=self.prepare_product_type_items(budget_outfit_list,"accessories")

            print("Starting the process of vision model analysis on products...")

            best_fashion_top=self.get_best_fashion_item(top_items_dict,outfit_set_summary)
            best_fashion_bottom=self.get_best_fashion_item(bottom_items_dict,outfit_set_summary)
            best_fashion_footwear=self.get_best_fashion_item(footwear_items_dict,outfit_set_summary)
            best_fashion_accessories=self.get_best_fashion_item(accessories_items_dict,outfit_set_summary)

            print("Successfully completed the vison model analysis, recevied the best products details...")
            print("Starting the process of creating fashion based outfit with best products...")

            final_fashion_based_outfit_output=self.get_final_fashion_outfit(budget_outfit_list,best_fashion_top,best_fashion_bottom,
                                     best_fashion_footwear,best_fashion_accessories,"Fashion based outfit")
            
            print("Successfully created the fashion based outfit...")
            print("Starting the process of creating budget based outfit...")

            final_budget_based_outfit=random.choice(budget_outfit_list)

            print("Successfully created the budget based outfit...")
            print("Starting the process of creating the outfit output(Fashion, Budget) for the outfit set...")
        
            final_budget_based_outfit_output=output_string.format(final_budget_based_outfit['outfit_set']['top']['name'],
            final_budget_based_outfit['outfit_set']['top']['price'],final_budget_based_outfit['outfit_set']['top']['product_url'],
            final_budget_based_outfit['outfit_set']['top']['image_url'],final_budget_based_outfit['outfit_set']['bottom']['name'],
            final_budget_based_outfit['outfit_set']['bottom']['price'],final_budget_based_outfit['outfit_set']['bottom']['product_url'],
            final_budget_based_outfit['outfit_set']['bottom']['image_url'],final_budget_based_outfit['outfit_set']['footwear']['name'],
            final_budget_based_outfit['outfit_set']['footwear']['price'],final_budget_based_outfit['outfit_set']['footwear']['product_url'],
            final_budget_based_outfit['outfit_set']['footwear']['image_url'],final_budget_based_outfit['outfit_set']['accessories']['name'],
            final_budget_based_outfit['outfit_set']['accessories']['price'],final_budget_based_outfit['outfit_set']['accessories']['product_url'],
            final_budget_based_outfit['outfit_set']['accessories']['image_url'],final_budget_based_outfit['outfit_set']['outfit_set_price'])

            print("Successfully created the output(Fashion, Budget) for the outfit set...")

            return final_budget_based_outfit_output+"\n"+final_fashion_based_outfit_output
            
        elif(len(budget_outfit_list)==1 and budget_pointer==1):
            print("!! Found only one choice of outfit for the user budget...")
            print("Starting the process of creating the only one budget outfit for the outfit set...")

            output_string=output_string.format(budget_outfit_list['outfit_set']['top']['name'],
            budget_outfit_list['outfit_set']['top']['price'],budget_outfit_list['outfit_set']['top']['product_url'],
            budget_outfit_list['outfit_set']['top']['image_url'],budget_outfit_list['outfit_set']['bottom']['name'],
            budget_outfit_list['outfit_set']['bottom']['price'],budget_outfit_list['outfit_set']['bottom']['product_url'],
            budget_outfit_list['outfit_set']['bottom']['image_url'],budget_outfit_list['outfit_set']['footwear']['name'],
            budget_outfit_list['outfit_set']['footwear']['price'],budget_outfit_list['outfit_set']['footwear']['product_url'],
            budget_outfit_list['outfit_set']['footwear']['image_url'],budget_outfit_list['outfit_set']['accessories']['name'],
            budget_outfit_list['outfit_set']['accessories']['price'],budget_outfit_list['outfit_set']['accessories']['product_url'],
            budget_outfit_list['outfit_set']['accessories']['image_url'],budget_outfit_list['outfit_set']['outfit_set_price'])

            print("Successfully created the only one budget outfit for the outfit set...")

            return output_string
        else:
            print("!! Not found any outfit for user budget...")
            print("Starting the process of creating non-budget based outfit with vision model...")
            print("Preparing the data for vision model...")

            top_items_dict=self.prepare_product_type_items(budget_outfit_list,"top")
            bottom_items_dict=self.prepare_product_type_items(budget_outfit_list,"bottom")
            footwear_items_dict=self.prepare_product_type_items(budget_outfit_list,"footwear")
            accessories_items_dict=self.prepare_product_type_items(budget_outfit_list,"accessories")

            print("Starting the process of vision model analysis on products...")

            best_fashion_top=self.get_best_fashion_item(top_items_dict,outfit_set_summary)
            best_fashion_bottom=self.get_best_fashion_item(bottom_items_dict,outfit_set_summary)
            best_fashion_footwear=self.get_best_fashion_item(footwear_items_dict,outfit_set_summary)
            best_fashion_accessories=self.get_best_fashion_item(accessories_items_dict,outfit_set_summary)

            print("Successfully completed the vison model analysis, recevied the best products details...")
            print("Starting the process of creating non-budget based outfit with best products...")

            final_non_budget_based_outfit_output=self.get_final_fashion_outfit(budget_outfit_list,best_fashion_top,best_fashion_bottom,
                                     best_fashion_footwear,best_fashion_accessories,"Non budget based outfit")
            
            print("Successfully created the non-budget based outfit...")
            
            return final_non_budget_based_outfit_output


    def _run(self, top_list:list, bottom_list:list,footwear_list:list,accessories_list:list,
             outfit_set_summary:list,user_budget:float) -> str:
        
        final_outfit_sets_output_string=""""""
        print("Shopping started...")
        for i in range(0,len(top_list)):
            
            print(f"Started the process of creating outfit for outfit set - {i+1}")

            outfit_output_string=self.shop_items(top_list[i],bottom_list[i],footwear_list[i],accessories_list[i],
                              outfit_set_summary[i],user_budget)
            final_outfit_sets_output_string=final_outfit_sets_output_string+"\nOutfit Set - {}".format(i+1)
            final_outfit_sets_output_string=final_outfit_sets_output_string+outfit_output_string

            print(f"Successfully created the outfit for outfit set - {i+1}")

        
        print('-'*80)
        print(final_outfit_sets_output_string)
        print('-'*80)
        return final_outfit_sets_output_string