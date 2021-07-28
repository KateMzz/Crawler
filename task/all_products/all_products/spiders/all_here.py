from requests.models import Response
import scrapy
import json
import requests



class AllHereSpider(scrapy.Spider):
    name = 'all_here'
    
    def start_requests(self): 
        categories = [
         '/api/c/women/_/N-7vf?page_size=9000',
         '/api/c/men/_/N-7tu?page_size=9000',
          '/api/c/accessories/_/N-8pb?page_size=9000']       
        for each_category in categories:
            yield scrapy.Request(url = f'https://shop.lululemon.com{each_category}', callback=self.parse_category)


    def parse_category(self, response):
        resp = json.loads(response.body)      
        items = resp.get('data')
        products = items.get('attributes').get('main-content')[0].get('records')
        pdp_bank = []        
        for product in products:
            product_endpoint = product.get("pdp-url")
            if product_endpoint not in pdp_bank:
                pdp_bank.append(product_endpoint)                    
                bazaar_id = product.get('bazaar-voice-id') 
                review_endpoint = f"https://api.bazaarvoice.com/data/batch.json?passkey=caOGkxt5ZGxRUy0oZU3zbSlV36IBwxAijWghipc2FSoQY&apiversion=5.5&displaycode=7834-en_us&resource.q0=reviews&filter.q0=isratingsonly%3Aeq%3Afalse&filter.q0=productid:eq:{bazaar_id}&filter.q0=contentlocale%3Aeq%3Aen_US&sort.q0=submissiontime%3Adesc&stats.q0=reviews&filteredstats.q0=reviews&include.q0=authors%2Cproducts%2Ccomments&filter_reviews.q0=contentlocale%3Aeq%3Aen_US&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen_US&filter_comments.q0=contentlocale%3Aeq%3Aen_US&limit.q0=30&offset.q0=0&limit_comments.q0=3"
                yield scrapy.Request(url=review_endpoint, callback=self.parse_rating, meta={'product_endpoint': product_endpoint, 'bazaar_id': bazaar_id})
            else:
                continue
            
    def parse_rating(self, response):
        product_endpoint = response.meta.get('product_endpoint')
        bazaar_id = response.meta.get('bazaar_id')
        resp = json.loads(response.body)
        prod_id = resp.get('BatchedResults').get('q0').get('Results')[0].get('ProductId')
        rating = resp.get('BatchedResults').get('q0').get('Includes').get('Products').get(prod_id).get('ReviewStatistics').get('AverageOverallRating')
        round_rating= round(float(rating),2)
        product_link = f"https://shop.lululemon.com/api{product_endpoint}"
        yield scrapy.Request(url=product_link, callback=self.parse_product, meta={'product_link': product_link,"round_rating": round_rating})


    def parse_product(self, response):
        rating = response.meta.get('round_rating') 
        product_link = response.meta.get('product_link')       
        resp = json.loads(response.body)
        data_new = resp.get('data').get('attributes')
        category = []
        first_categ_part = data_new.get('refinement-crumbs').get('ancestors')
        sec_categ_part = data_new.get('refinement-crumbs').get('label')
        for label in first_categ_part:
            new_label = label.get('label')
            category.append(new_label)
        category.append(sec_categ_part)
        description = data_new.get('product-summary').get('why-we-made-this')
        time = data_new.get('product-summary').get('product-last-sku-addition-date-time')
        icon = data_new.get('product-carousel')[0].get('image-info')[0]
        reviews = data_new.get('purchase-attributes').get('reviews').get('count')                      
        child_skus = data_new.get('child-skus')
        for variant in child_skus:                
            size = variant.get('size')
            color_code = variant.get('color-code')
            sec_color_code = data_new.get('product-carousel')
            
            for codes in sec_color_code:
                code = codes.get('color-code')
                
                if code == color_code:
                    color_name = codes.get('swatch-color-name')
                    break

            sku = variant.get('id')
            price = variant.get('price-details').get('list-price')           
            sale_price = variant.get('price-details').get('sale-price')
            if not sale_price:
                sale_price = ""
            else:
                sale_price = sale_price
            
            in_stock = variant.get('available')
            if in_stock:
                in_stock = 'YES'
            else:
                in_stock = 'NO'                    

            brand = "lululemon"
                    
            yield{
                "brand": brand,
                "category": category,
                "description": description,
                "price": price,
                "product_link": product_link,
                "time": time,
                "size": size,
                "color": color_name,
                "icon": icon,
                "rating": rating,
                "reviews": reviews,
                "sku":  sku,
                "sale_price": sale_price,
                "in_stock": in_stock
            }

        

        # has_next = resp.get("has_next")
        # if has_next:
        #     next_page_num = resp.get('page') +1
        #     yield scrapy.Request(
        #         url=f'https://shop.lululemon.com/api/c/women/_/N-7vf?page={next_page_num}',
        #         callback=self.parse
        #     )

                
       
