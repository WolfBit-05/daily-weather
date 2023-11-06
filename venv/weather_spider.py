import scrapy
from transformers import pipeline
import json
import os
import re

class WeatherSpider(scrapy.Spider):
    name = "weather_data"
    allowed_domains = ["mausam.imd.gov.in"]
    start_urls = ["https://mausam.imd.gov.in/imd_latest/contents/Todaysweather_mc.php?id=13"]

    @staticmethod
    def preprocess_value(value, data_type):
        if not value or not isinstance(value, str):
            return None  # or any other default value as per your requirement

        if value in {'NIL', '--'}:
            return 0.0 if data_type == 'float' else 0

        cleaned_value = re.findall(r"\d+\.\d+|\d+", value)
        if cleaned_value:
            try:
                return float(cleaned_value[0])
            except ValueError:
                return None

        return None

    
    def generate_weather_report(self, data):
        # Extract the data
        max_temp = data.get('Max Temp (°C)')
        dep_from_normal_max = data.get('Dep. from Normal(Max. temp)')
        min_temp = data.get('Min Temp (°C)')
        dep_from_normal_min = data.get('Dep. from Normal(Min. temp)')
        rh_0830 = data.get('RH at 0830IST')
        rh_1730 = data.get('RH at 1730IST')
        rainfall_mm = data.get('Rainfall (mm)')
        station = data.get('Station')

        if max_temp is not None:
            max_temp = float(max_temp)
        else:
            max_temp = 0.0  # Replace with a suitable default value

        if dep_from_normal_max is not None:
            dep_from_normal_max = int(dep_from_normal_max)
        else:
            dep_from_normal_max = 0  # Replace with a suitable default value

        if min_temp is not None:
            min_temp = float(min_temp)
        else:
            min_temp = 0.0  # Replace with a suitable default value

        if dep_from_normal_min is not None:
            dep_from_normal_min = int(dep_from_normal_min)
        else:
            dep_from_normal_min = 0  # Replace with a suitable default value

        if rh_0830 is not None:
            rh_0830 = int(rh_0830)
        else:
            rh_0830 = 0  # Replace with a suitable default value

        if rh_1730 is not None:
            rh_1730 = int(rh_1730)
        else:
            rh_1730 = 0  # Replace with a suitable default value

        if rainfall_mm is not None:
            rainfall_mm = float(rainfall_mm)
        else:
            rainfall_mm = 0.0  # Replace with a suitable default value

        # Create scenarios and tone of the paragraph based on weather conditions
        if max_temp > 30:
            scenario = "hot"
            tone = "Climate's so warm out there!"
        elif max_temp > 25:
            scenario = "warm"
            tone = "Enjoy the warm weather today!"
        else:
            scenario = "mild"
            tone = "It's a pleasant day with mild temperatures."

        if dep_from_normal_max > 0:
            departure_max = f" which is {dep_from_normal_max}°C warmer"
        elif dep_from_normal_max < 0:
            departure_max = f" which is {abs(dep_from_normal_max)}°C cooler"
        else:
            departure_max = " temperatures are normal"

        if min_temp == 'NA':
            min_temp_desc = "The minimum temperature data is not available."
        else:
            min_temp_desc = f"The minimum temperature is {min_temp}°C"

        if dep_from_normal_min > 0:
            departure_min = f", {dep_from_normal_min}°C warmer"
        elif dep_from_normal_min < 0:
            departure_min = f", {abs(dep_from_normal_min)}°C cooler"
        else:
            departure_min = "temperatures are normal"

        if rh_0830 > 70 and rh_1730 < 60:
            humidity_desc = "It starts off a bit humid in the morning but becomes drier later in the day."
        elif rh_0830 < 60 and rh_1730 > 70:
            humidity_desc = "The day begins with lower humidity, but it becomes more humid in the evening."
        else:
            humidity_desc = "The humidity levels remain relatively stable throughout the day."

        if rainfall_mm > 5:
            rainfall_desc = f"Expect heavy rainfall today with {rainfall_mm} mm of precipitation."
        elif rainfall_mm > 0:
            rainfall_desc = f"We might see some light rain today with {rainfall_mm} mm of precipitation."
        else:
            rainfall_desc = "No significant rainfall is expected today."

        # Create the paragraph-style weather report
        template = f"At {station}, the weather today is as follows:\n\n" \
                   f"The maximum temperature is expected to reach {max_temp}°C, \n\n" \
                   f"{departure_max} than usual for this time of year.\n\n" \
                   f"{tone} {min_temp_desc}\n\n" \
                   f"{departure_min} than the typical temperature for this time of year.\n\n" \
                   f"{humidity_desc}\n\n" \
                   f"{rainfall_desc}"

        report_length = template.replace('\n','')
        # Use Hugging Face pipeline for text generation
        text_generator = pipeline("text-generation", model="gpt2")

        # Generate text based on the template and data
        generated_text = text_generator(template, max_length=104, num_return_sequences=1, do_sample=True)

        return generated_text[0]['generated_text']

    # Initialize an empty list to store the extracted data
    extracted_data = []

    def parse(self, response):

        # Locate the table using the HTML structure
        table = response.xpath('//table[tr[td[contains(text(), "Station")]]]')

        # Iterate through rows and extract data
        for row in table.xpath('.//tr[td]'):
            item = {
                'Station': row.xpath('.//td[1]/text()').get(),
                'Max Temp (°C)': self.preprocess_value(row.xpath('.//td[2]/text()').get(), 'float'),
                'Dep. from Normal(Max. temp)': self.preprocess_value(row.xpath('.//td[3]/text()').get(), 'int'),
                'Min Temp (°C)': self.preprocess_value(row.xpath('.//td[4]/text()').get(), 'float'),
                'Dep. from Normal(Min. temp)': self.preprocess_value(row.xpath('.//td[5]/text()').get(), 'int'),
                'RH at 0830IST': self.preprocess_value(row.xpath('.//td[6]/text()').get(), 'int'),
                'RH at 1730IST': self.preprocess_value(row.xpath('.//td[7]/text()').get(), 'int'),
                'Rainfall (mm)': self.preprocess_value(row.xpath('.//td[8]/text()').get(), 'float'),
            }
            self.extracted_data.append(item)  # Append the item to the list

        # Pass the extracted data dynamically for text generation
        for data in self.extracted_data:
            generated_report = self.generate_weather_report(data)
            data['generated_report'] = generated_report  # Include the generated report in the data dictionary
            self.logger.info(generated_report)  # Use self.logger instead of print
            yield {
                'station_data': data,
                'generated_report': generated_report
            }
        #check if the json file already exists
        if not os.path.exists('weather_data.json'):
            #save the data as JSON
            with open('weather_data.json', 'w') as f:
                json.dump(self.extracted_data, f, indent=4)