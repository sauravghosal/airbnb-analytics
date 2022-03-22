# Airbnb Scraper

### Purpose

The purpose of this project is to scrape occupancy, pricing, and other related listing data for tiny houses that are available on AirBnb. [This link](https://www.airbnb.com/stays/tiny-houses) provides an overview of the tiny house listings, as well as the most popular locations on Airbnb.

### Approach

This scraper hits Airbnb's API to query for tiny house listing data. The first API fetches the names of the top listings for each location, which I selected as Florida, Georgia, and North Carolina, along with basic listing info, like bedrooms, baths, reviews, amenities, city, and superhost status. This API is only hit once to receive the initial tiny houses for which to track occupancy. I have capped the number of tiny houses for which to track occupancy at 100 per location; thus, 100 x 3 yields tracking for 300 tiny houses.

The second API fetches the occupancy data for a particular listing. This API is hit every day through a cron job that runs at 8 pm on an Amazon EC2 instance. Currently, we do not fetch pricing data, which would be a good extension to this project. The data is written to an Excel spreadsheet that is uploaded to a shared Dropbox folder so that clients can see the program running every night as expected; however, this will be removed soon to allow for the data to be directly ingested into an AWS RDS database.

### Database Schema

TODO: insert image

### Website

Visit [this website](http://ghosalre.com/) for visualizations on this data!
