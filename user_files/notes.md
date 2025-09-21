# Notes

So...

first we get platform info - see https://api-docs.igdb.com/?python#platform

will need to get all the enums and such first

then I can list how many platforms there are using platform/count

so I can get detailed info about each platform now, I guess, and save that into main output file

but then when it comes to getting game info, I only want platforms I'm interested in - that's where this next bit comes in

then get platforms I'm interested in from csv file - DECISION NEEDED: am I going to map names from mister docs to names/IDs from IGDB API, or am I going to attempt to do it automatically and then spit out errors. I think for now I can just manually match and then do an enhancement later. 

what if there's no 'platforms' file? I think just get all platform info supported by IGDB, I guess...

get top n games per platform by rating - just game id and platform id

then get games I specifically know I want - can do this with just a new csv file called 'games', one column for platform (see above about how to match) one for game name - again just game id and platform id

then once we've got the IDs we can get the specific fields wanted from game api including getting images from URLs

wait. that's all way too complex. we can just use expanders within the query in order to get all the information we need. 

platform query:

fields 
  name,
  abbreviation,
  alternative_name,
  generation,
  platform_family.name,
  platform_logo.alpha_channel,
  platform_logo.animated,
  platform_logo.image_id,
  platform_logo.url,
  platform_logo.width,
  platform_logo.height,
  platform_type.name,
  slug,
  summary,
  websites.trusted,
  websites.type.type,
  websites.url
;

where id = (25,63,26,373,59,33,22,79,80,4,18,7,30,64,35,32,19,86,150);

sort id asc;

limit 500;

But. I don't seem to get the 'summary'; it's supposed to be the summary from the FIRST version of the platform, so I think I need to figure out how to limit versions to just the first if I want that text - it might need a separate call to different APIs to find that out. But that's ONLY IF I really want that info, and I don't think I do. 

game query - WORK IN PROGRESS!!!!! NEEDS REFINING!!!!:

fields
  age_ratings,
  aggregated_rating,
  aggregated_rating_count,
  alternative_names,
  artworks,
  bundles,
  collections,
  cover,
  created_at,
  dlcs,
  expanded_games,
  expansions,
  external_games,
  first_release_date,
  forks,
  franchise,
  franchises,
  game_engines,
  game_localizations,
  game_modes,
  game_status,
  game_type,
  genres,
  hypes,
  involved_companies,
  keywords,
  language_supports,
  multiplayer_modes,
  name,
  parent_game,
  platforms,
  player_perspectives,
  ports,
  rating,
  rating_count,
  release_dates,
  remakes,
  remasters,
  screenshots,
  similar_games,
  slug,
  standalone_expansions,
  storyline,
  summary,
  tags,
  themes,
  total_rating,
  total_rating_count,
  updated_at,
  url,
  version_parent,
  version_title,
  videos,
  websites
;
sort rating desc; 

where platforms = (25);

limit 20; 


Also. Something else to think about, esp. regarding the early computer stuff - multiplatform releases. the same game might have been released on different systems, and I really only want the 'best' version of each game. like... Flimbo's Quest https://www.igdb.com/games/flimbos-quest: which platform has the definitive version of this game? Or Speedball 2 https://www.igdb.com/games/speedball-2-brutal-deluxe: that came out on a FORKTON of systems.