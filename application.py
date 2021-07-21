from flask import Flask
import requests
from flask_restful import  Resource, Api,reqparse 
import json
from bs4 import BeautifulSoup
from flask_cors import CORS
import logging
from flask import jsonify
from textblob import TextBlob
import sys, tweepy
from json.decoder import JSONDecodeError


application =  Flask(__name__)
CORS(application)
cors = CORS(application,resources={r"/*":{"origins":"*"}})
api = Api(application)



class home(Resource):
    def get(self):
        return "Dhiraj Santander Python Api"


######################################################################################################
# This class Avatar gets the Avatar from Wikipedia to show  when the user search for Actor or Director.
# Here i have use BeautifulSoup Python Library to extract data from html files.
# I then extract the image from the html node and return the image src. 
######################################################################################################

class avatar(Resource):
   
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('artist', type=str)
        params = parser.parse_args()

    
        url = 'https://en.wikipedia.org/wiki/' + params.artist
        content = requests.get(url).content
        soup = BeautifulSoup(content,'lxml') 

        try:
            try:
                avatar = soup.find('table', {"class": "infobox biography vcard"}).img['src']
                #print(image_tags)  
                return jsonify({'avatar':avatar})
                                       
            except:
                avatar = soup.find('table', {"class": "infobox vcard"}).img['src']
                return jsonify({'avatar':avatar})
        except:
           return jsonify({'avatar':"404"})
       


#################################################################################################################################################################################################
# This movieList class is the main class which is responsible for pulling all the data from diffrenct source and merge into single list.
# In this API i have call 3 different Api to extract the movie information.
# First i have call getMoviesName function which pulls all the movies name that the actor/director involved in which store in a single list/array.
# Second i have call searchMovie function which gets the movie id from the movies name.
# Third i have call omdb function to get all the movie details of the movie by providing the movie id.
# I have create a loop to get the data from 3 Api which provids movie name,movie id and movie details and merge them into a single multidimension array/dictionary.
# I have use try except for exception handling as because if any of the api fails to get the movie id or movie details it will not break the loop and pass on to next to keep on pulling the data
# And finally it will convert multidimension array into json array for processing in frontend app.
##################################################################################################################################################################################################

class movieList(Resource):
   

    def get(self):

         parser = reqparse.RequestParser()
         parser.add_argument('artist', type=str)
         parser.add_argument('role', type=str)
         params = parser.parse_args()

        
         movieList={}
         movies = self.getMoviesName(params.artist,params.role)


         try:
            for m in range(1,len(movies)):
             
             try:
                id=self.searchMovie(movies[m])
                #print(id) 
             except:
                pass
             
             try:
                ml = self.omdb(id)
                movieList.update({movies[m]:ml})
             except:
                 pass         
             
         except JSONDecodeError as e:
             pass

         
         return jsonify({'movie':movieList})


################################################################################################################
# This function scrap all the movies name that the actor/director involved in from the website www.filmcrave.com.
# I also have use BeautifulSoup python library to get the movies name from html node.
# I then have to create a for loop in order to get all the movies name from all the pages passing the page id.
# Then it will return a movie array to the main function. 
################################################################################################################

    def getMoviesName(self,artist,role):
         movie = []

         director=''
         actor=''

         if role == "actor":
             actor = str(artist)
         elif role == "director":
             director = str(artist)
         
         
         for i in range(7):
            url = 'https://www.filmcrave.com/search_films.php?filmname=&director='+director+'&actor='+actor+'&genre=&mpaa=&decade=&submit=Search&page='+ str(i) +'#results'
            content = requests.get(url).content
            soup = BeautifulSoup(content,"html.parser")
            for p in soup.find_all('h3',class_='xlarge'):
                movie.append(p.text)

         return movie
         
  

#######################################################################################
# This function calls the IMDB move Api and return the movie ID based on the movie name 
#######################################################################################  
     
    def searchMovie(self,movie):
        url = "https://imdb-internet-movie-database-unofficial.p.rapidapi.com/search/"+movie

        headers = {
            'x-rapidapi-key': "894d1306d5msh8776a666b2fa32dp1c6ef0jsnceeb5910e75f",
            'x-rapidapi-host': "imdb-internet-movie-database-unofficial.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers)
        res = json.loads(response.text)
        movieId = res["titles"][0]["id"]

        return movieId


######################################################################################
# Similary this funtions gets the movie id as param and return the full movie details.
# I have build an array by extracting onley the data what is most relevant.
######################################################################################

    def omdb(self,id):
       
        details=[]
        
        url = "http://www.omdbapi.com"

        querystring = {"i":id,"apikey":"2873cb68"}

        headers = {
            'x-rapidapi-key': "894d1306d5msh8776a666b2fa32dp1c6ef0jsnceeb5910e75f",
            'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        res = json.loads(response.text)
        details.append((res['Year'],res['Released'],res['Genre'],res['Director'],res['Poster'],res['Awards'],res['Actors']))
        return details
        #print(res) 





############################################################################################################################################################
# This Class pulls the tweets from the twitter api by the number of given sample and analyse the sentiments out of it
# Here i have use TextBlob machine learning library from python for processing textual data.
# Every sets of tweet has a polarity, polarity is way to calculate the statement in the given tweets.
# If the statement is grater then 0 then we mark them as a positive statement and if the statement in less then 0 then we mark them as a negative statement.
# If the statement is 0 then we mark as a neutral statement.

# So in this program i have called the twitter api to get the given no of tweets and call the TextBlob api to get the polarity of that tweets.
# Then based on the polarity i have calculate the positive, negative and neutral sentiments.
# I then created a function percentage to calculate the percentage of the sentiments of the tweets.
# Then it will return the positive, negative, neutral and polarity in the percentage to display sentiment in the frontend app.
############################################################################################################################################################

class sentiment(Resource):

    def percentage(self, part, whole):
        return 100 * float(part)/float(whole)


    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('hashtag', type=str)
        parser.add_argument('tweetsCount', type=int)
        params = parser.parse_args()


        positive = 0
        negative = 0
        neutral = 0
        polarity = 0

        tweets =  self.authTwitter(params)


        for tweet in tweets:
         analysis = TextBlob(tweet.text)
         polarity += analysis.sentiment.polarity


         if analysis.sentiment.polarity == 0 :
            neutral += 1
         elif analysis.sentiment.polarity  < 0.00 :
            negative += 1
         elif analysis.sentiment.polarity  > 0.00 :
            positive += 1
      

        positive = self.percentage(positive, params.tweetsCount)
        negative = self.percentage(negative , params.tweetsCount)
        neutral = self.percentage(neutral,params.tweetsCount)
        polarity = self.percentage(polarity,params.tweetsCount)
       

        #getting the only 2 digits 
        positive = format(positive, '.2f')
        neutral = format(neutral, '.2f')
        negative = format(negative, '.2f')

        output = {'Polarity' : polarity ,'Positive': positive,'Neutral' : neutral ,'Negative':negative}
        return jsonify({'result':output})




###############################################################################
# This function calls the twitter api and get the tweets from the given number.
###############################################################################

    def authTwitter(self,params):
        

        consumerKey = "Q8QlvmO2BvdKJBlpeLOiVYT4M"
        consumerSecret = "wvhaELkrcYfDS5OLjb7tal3VzFdWM8LjzfurLcSKYmAZmH2VhR"
        accessToken = "1351854568834015233-4SPx5ybr4GQvTuzXw8XSgImtsFkBsD"
        accessTokenSecret= "asuLTrkWzQGfQTI2cWti3OVAiLlJorMIs48MZyHDbBtqw"


        auth = tweepy.OAuthHandler(consumer_key= consumerKey, consumer_secret = consumerSecret)
        auth.set_access_token(accessToken, accessTokenSecret)
        api = tweepy.API(auth)

        tweets  = tweepy.Cursor(api.search , q = params.hashtag).items(params.tweetsCount)

        return tweets



api.add_resource(home,'/')
api.add_resource(avatar,'/avatar')
api.add_resource(movieList,'/movie')
api.add_resource(sentiment,'/sentiment', methods = ['POST'])


if __name__ == '__main__':
    application.run(host="0.0.0.0",port=80,debug=True)


##########################################################################
# Dhiraj Santander Project @ 2021
##########################################################################
