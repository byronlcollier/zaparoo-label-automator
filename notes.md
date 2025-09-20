# Notes

So...

first we get platform info - see https://api-docs.igbd.com/?python#platform

will need to get all the enums and such first

then I can list how many platforms there are using platform/count

so I can get detailed info about each platform now, I guess, and save that into main output file

but then when it comes to getting game info, I only want platforms I'm interested in - that's where this next bit comes in

then get platforms I'm interested in from csv file - DECISION NEEDED: am I going to map names from mister docs to names/IDs from IGDB API, or am I going to attempt to do it automatically and then spit out errors. I think for now I can just manually match and then do an enhancement later. 

what if there's no 'platforms' file? I think just get all platform info supported by IGDB, I guess...

get top n games per platform by rating - just game id and platform id

then get games I specifically know I want - can do this with just a new csv file called 'games', one column for platform (see above about how to match) one for game name - again just game id and platform id

then once we've got the IDs we can get the specific fields wanted from game api including getting images from URLs
