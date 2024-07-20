from time import sleep
import concurrent.futures
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import time
import os
import requests

#####################################################################################

# Match Folder
folder_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

#####################################################################################

# Scrape data with CSS Selector
def get_element_text(driver, selector):
    element = driver.find_element(By.CSS_SELECTOR, selector)
    return element.get_attribute('textContent').strip()

#####################################################################################

# Process Player Data from 'status'
def extract_player_data(output):
    player_data = []
    lines = output.splitlines()

    for line in lines:
        match = re.match(r"#\s*(\d+)\s+(\d+)\s+\"([^\"]+)\"\s+(STEAM_\d:\d:\d+)\s+(\d+:\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\d+)", line)
        if match:
            userid = match.group(1)
            name = match.group(3)
            steam_id = match.group(4)
            ping = match.group(6)
            loss = match.group(7)

            steam_id_parts = steam_id.split(":")
            if len(steam_id_parts) == 3:
                steam64_id = "7656" + str(int(steam_id_parts[2]) * 2 + int(steam_id_parts[1]) + 1197960265728)

            player_data.append((userid, name, steam64_id, ping, loss))

    return player_data

#####################################################################################

# Download profile images
def download_profile_image(player, avatar_url):
    player_name_normalized = player[1].replace(" ", "_")
    image_extension = os.path.splitext(avatar_url)[1]
    image_filename = f"{player_name_normalized}{image_extension}"
    image_path = os.path.join(folder_name, image_filename)

    if avatar_url:
        print(avatar_url)
        response = requests.get(avatar_url)
        if response.status_code == 200:
            with open(image_path, 'wb') as image_file:
                image_file.write(response.content)
            print(f"Profile image downloaded for {player[1]}")
        else:
            print(f"Failed to download profile image for {player[1]}")
    else:
        print(f"No avatar URL available for {player[1]}")

#####################################################################################

# Create HTML Report
def generate_html_report(player_data, image_filename=None):
    # Generate HTML content for player info
    html_content = """
    <html>
    <head>
        <title>Player Stats Report</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            p.card-text {
                margin: 0; /* Set margin to 0 for p elements */
            }

            /* Custom card styling */
            .player-card {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                transition: background-color 0.3s ease;
            }

            /* Hover effect for player cards */
            .player-card:hover {
                background-color: #e0f0ff; 
                border-color: #99c2ff; 
            }

            /* Center the player cards */
            .row.row-cols-2.g-3 .col {
                display: flex;
                justify-content: center;
            }

            /* Add space between player cards */
            .row.row-cols-3.g-3 .col:not(:last-child) {
                margin-right: 15px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center">Player Stats Report</h1>
    """

    # Add HTML content for player cards
    html_content += """
        <div class="row row-cols-3 g-2">
        <br>
    """
    
    # Loop through each player's data
    for player in player_data:
        image_filename = f"{player[0].replace(' ', '_')}.jpg"
        html_content += f"""
            <div class="col">
                <div class="card mb-3 player-card">
                    <div class="card-body">
                        <h5 class="card-title">{player[0]}</h5>
                        <div class="text-center">
                            <img src="{image_filename}" alt="{player[0]}'s Image" style="max-width: 200px;">
                        </div>
                        <p class="card-text">Current Rank: {player[1]}</p>
                        <p class="card-text">Highest Rank: {player[2]}</p>
                        <p class="card-text">Win Rate: {player[3]}</p>
                        <p class="card-text">Leetify Rating: {player[4]}</p>
                        <p class="card-text">T Rating: {player[5]}</p>
                        <p class="card-text">CT Rating: {player[6]}</p>
                        <p class="card-text">Aim: {player[7]}</p>
                        <p class="card-text">Utility: {player[8]}</p>
                        <p class="card-text">Positioning: {player[9]}</p>
                        <p class="card-text">Opening Duels: {player[10]}</p>
                        <p class="card-text">Clutching: {player[11]}</p>
                    </div>
                </div>
            </div>
        """

    # Close the HTML content
    html_content += """
        </div>
    </div>
    """

    # Add HTML content for charts
    chart_html = """
        <h2 class="text-center">Charts</h2>
        <div class="text-center">
            <img src="aim_values_graph.png" alt="Aim Values Graph" style="max-width: 800px;">
            <img src="utility_graph.png" alt="Utility Values Graph" style="max-width: 800px;">
            <img src="positioning_graph.png" alt="Positioning Values Graph" style="max-width: 800px;">
            <img src="opening_duels_graph.png" alt="Opening Duels Values Graph" style="max-width: 800px;">
            <img src="clutching_graph.png" alt="Clutching Values Graph" style="max-width: 800px;">
        </div>
    """

    # Combine the HTML content
    html_content += chart_html + """
    </body>
    </html>
    """

    # Write the HTML content to a file
    html_filename = os.path.join(folder_name, 'report.html')
    with open(html_filename, 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

#####################################################################################

# Main Function
def main():
    start_time = time.time()
    avatar_urls = []  

    try:
        # Create a folder with the current date and time
        os.makedirs(folder_name)

        # Read the command_output from the text file
        with open('command_output.txt', 'r', encoding='utf-8') as file:
            command_output = file.read()

        player_data = extract_player_data(command_output)

        # Open files within the folder
        with open(os.path.join(folder_name, 'player_info.txt'), 'w', encoding='utf-8') as txt_file, open(os.path.join(folder_name, 'player_data.csv'), 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Name', 'Current Rank', 'Highest Rank', 'Win Rate', 'Leetify Rating', 'T Rating', 'CT Rating', 'Aim', 'Utility', 'Positioning', 'Opening Duels', 'Clutching'])

            aim_values = []  
            image_filename = None  

            for i, player in enumerate(player_data):
                print()
                print("Name:", player[1])
                txt_file.write(f"Name: {player[1]}\n")

                steam64_id = player[2]
                profile_url = f"https://leetify.com/app/profile/{steam64_id}"

                options = Options()
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--headless')
                options.add_argument('--disable-features=WebPlatformDependentDate')
                options.add_argument('log-level=3')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])

                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=options
                )

                driver.get(profile_url)

                sleep(8)

                selectors = {
                    "profile_name": "body > app-root > app-public-container > main > div > app-profile > app-profile-hero > header > div.rank-and-name > h1",
                    "alt_name": "body > app-root > app-public-container > main > div > app-profile > app-profile-hero > header > div.rank-and-name > app-rank-icon.--matchmaking.ng-star-inserted > img",
                    "alt_name_after": "#rank-history-and-activity > header > div > app-rank-icon.--matchmaking.ng-star-inserted > img",
                    "avatar": ".avatar-wrapper .background img",
                    "highest_rank": "#rank-history-and-activity > header > div > div:nth-child(1) > app-rank-icon > app-cs-rating > div > div"
                }

                elements = {}
                for key, selector in selectors.items():
                    elements[key] = driver.execute_script(f'return document.querySelector("{selector}");')

                try:
                    profile_name_element = elements["profile_name"]
                    profile_name = profile_name_element.text.strip()
                except AttributeError:
                    profile_name = "N/A (No Profile)"

                try:
                    alt_name_element = elements["alt_name"]
                    alt_name = alt_name_element.get_attribute("alt") if alt_name_element else None
                except AttributeError:
                    alt_name = "N/A"

                try:
                    alt_name_after_element = elements["alt_name_after"]
                    alt_name_after = alt_name_after_element.get_attribute("alt") if alt_name_after_element else None
                except AttributeError:
                    alt_name_after = "N/A"

                try:
                    avatar_element = elements["avatar"]
                    avatar_url = avatar_element.get_attribute("src") if avatar_element else None
                    avatar_urls.append(avatar_url)
                except AttributeError:
                    avatar_urls.append(None)


                cs_rating_selector = (
                    "body > app-root > app-layout > main > app-profile > app-profile-hero > "
                    "header > div.rank-and-name > div > app-rank-icon > app-cs-rating > "
                    "div > div"
                )

                try:
                    cs_rating_element = driver.find_element(By.CSS_SELECTOR, cs_rating_selector)
                    cs_rating = cs_rating_element.text.strip() if cs_rating_element else "N/A"
                except NoSuchElementException:
                    print("CS Rating Text not found")

                try:
                    highest_rank_element = elements["highest_rank"]
                    highest_rank = highest_rank_element.text.strip()
                except AttributeError:
                    highest_rank = "N/A (No Data)"


                svg_selectors = [
                    "#stats-overview > div > div.meta > div.win-rate > app-score-circle-outline > svg > text",
                    "#stats-overview > div > div.meta > div.ratings > div.total > app-score-circle-outline > svg > text",
                    "#stats-overview > div > div.meta > div.ratings > div.side-ratings > div:nth-child(1) > app-score-circle-outline > svg > text",
                    "#stats-overview > div > div.meta > div.ratings > div.side-ratings > div:nth-child(2) > app-score-circle-outline > svg > text",
                    "#stats-overview > div > div.stats > div:nth-child(3) > div > div.value",
                    "#stats-overview > div > div.stats > div:nth-child(5) > div > div.value",
                    "#stats-overview > div > div.stats > div:nth-child(7) > div > div.value",
                    "#stats-overview > div > div.stats > div:nth-child(9) > div > div.value",
                    "#stats-overview > div > div.stats > div:nth-child(11) > div > div.value",
                    "body > app-root > app-layout > main > app-profile > app-profile-hero > header > div.rank-and-name > div > app-rank-icon > app-cs-rating > div > div"
                ]

                svg_text = []
                for svg_selector in svg_selectors:
                    try:
                        svg_text.append(get_element_text(driver, svg_selector))
                    except NoSuchElementException:
                        svg_text.append("N/A")

                # Terminal
                print("CS2 Current Rating:", svg_text[9])
                print("CS2 Highest Rating:", highest_rank)
                print("Win Rate:", svg_text[0])
                print("Leetify Rating:", svg_text[1])
                print("T Rating:", svg_text[2])
                print("CT Rating:", svg_text[3])
                print("Aim:", svg_text[4])
                print("Utility:", svg_text[5])
                print("Positioning:", svg_text[6])
                print("Opening Duels:", svg_text[7])
                print("Clutching:", svg_text[8])

                # Text File
                txt_file.write(f"CS2 Current Rating: {svg_text[9]}\n")
                txt_file.write(f"CS2 Highest Rating: {highest_rank}\n")
                txt_file.write(f"Win Rate: {svg_text[0]}\n")
                txt_file.write(f"Leetify Rating: {svg_text[1]}\n")
                txt_file.write(f"T Rating: {svg_text[2]}\n")
                txt_file.write(f"CT Rating: {svg_text[3]}\n")
                txt_file.write(f"Aim: {svg_text[4]}\n")
                txt_file.write(f"Utility: {svg_text[5]}\n")
                txt_file.write(f"Positioning: {svg_text[6]}\n")
                txt_file.write(f"Opening Duels: {svg_text[7]}\n")
                txt_file.write(f"Clutching: {svg_text[8]}\n")
                txt_file.write("\n")  # Add an empty line for separation

                # CSV File
                csv_writer.writerow([
                    player[1],
                    cs_rating,
                    highest_rank,
                    svg_text[0],
                    svg_text[1],
                    svg_text[2],
                    svg_text[3],
                    svg_text[4],
                    svg_text[5],
                    svg_text[6],
                    svg_text[7],
                    svg_text[8]
                ])

                sleep(0.5)
                driver.quit()

            # Download profile images concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(download_profile_image, player, avatar_url) for player, avatar_url in zip(player_data, avatar_urls)]
                concurrent.futures.wait(futures)

    except Exception as e:
        print("An error occurred:", e)

#----------------------------------------------------------------------------#
        
    # Read the player data from the CSV file
    try:
        player_data = []
        with open(os.path.join(folder_name, 'player_data.csv'), 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  
            for row in csv_reader:
                player_data.append(row)

#----------------------------------------------------------------------------#
        # Extract aim values and player names
        aim_values = []
        player_names = []
        for player in player_data:
            aim_value = player[7] 
            if aim_value != 'N/A':
                aim_values.append(float(aim_value))
                player_names.append(player[0])  

        # Sort players in ascending order based on aim values
        sorted_players = [player for _, player in sorted(zip(aim_values, player_names))]

        # Sort aim values accordingly
        sorted_aim_values = sorted(aim_values)

        # Plot 'Aim' values using matplotlib
        plt.figure(figsize=(10, 6))
        bars = plt.bar(sorted_players, sorted_aim_values)
        plt.xlabel('Player Name')
        plt.ylabel('Aim Value')
        plt.title('Aim Values of Players (Ascending Order)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Display aim values 
        for bar, aim_value in zip(bars, sorted_aim_values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{int(aim_value)}', ha='center', va='bottom')

        # Save the graph as an image
        plt.savefig(os.path.join(folder_name, 'aim_values_graph.png'))

        # Show the plot
        # plt.show()
#----------------------------------------------------------------------------#
        
        # Define the metric names 
        metrics = ['Utility', 'Positioning', 'Opening Duels', 'Clutching']
        metric_indices = [8, 9, 10, 11]

        # Loop through each metric
        for metric_name, metric_index in zip(metrics, metric_indices):
            # Extract metric values and player names
            metric_values = []
            player_names = []
            
            for player in player_data:
                value = player[metric_index]
                if value != 'N/A':
                    metric_values.append(float(value))
                    player_names.append(player[0])  
            
            # Sort players and metric values
            sorted_players = [player for _, player in sorted(zip(metric_values, player_names))]
            sorted_metric_values = sorted(metric_values)
                      
            # Create the plot
            plt.figure(figsize=(10, 6))
            bars = plt.bar(sorted_players, sorted_metric_values)
            plt.xlabel('Player Name')
            plt.ylabel(f'{metric_name} Value')
            plt.title(f'{metric_name} Values of Players (Ascending Order)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Display metric values on top of bars without decimal points
            for bar, value in zip(bars, sorted_metric_values):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{int(value)}', ha='center', va='bottom')
            
            # Save the graph as an image
            filename = f'{metric_name.lower().replace(" ", "_")}_graph.png'
            plt.savefig(os.path.join(folder_name, filename))
            
            # Show the plot
            # plt.show()

        generate_html_report(player_data, image_filename)  

        #End Timer
        end_time = time.time()
        tot_time = (f"Total time: {end_time - start_time}")
        tot_time = round(end_time - start_time, 2)
        print("Elapsed time: " + str(tot_time))

    except Exception as e:
        print("An error occurred:", e)

#####################################################################################

if __name__ == "__main__":
    main()