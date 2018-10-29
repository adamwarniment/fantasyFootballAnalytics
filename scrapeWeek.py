from bs4 import BeautifulSoup
from urllib import urlopen
import MySQLdb


teamNameLookup = ['New York Jets', 'Minnesota Vikings', 'Baltimore Ravens', 'Los Angeles Rams', 'Cleveland Browns', 'Jacksonville Jaguars', 'Miami Dolphins', 'Washington Redskins', 'Carolina Panthers', 'Chicago Bears', 'Cincinnati Bengals', 'Denver Broncos', 'Philadelphia Eagles', 'Detroit Lions', 'Pittsburgh Steelers', 'Tennessee Titans', 'Kansas City Chiefs', 'New England Patriots', 'Tampa Bay Buccaneers', 'Atlanta Falcons', 'Dallas Cowboys', 'Houston Texans', 'Seattle Seahawks', 'Green Bay Packers', 'New York Giants', 'Arizona Cardinals', 'Indianapolis Colts', 'San Francisco 49ers', 'Buffalo Bills', 'Los Angeles Chargers', 'Oakland Raiders', 'New Orleans Saints']
teamIDLookup = ['NYJ', 'MIN', 'BAL', 'LA', 'CLE', 'JAX', 'MIA', 'WAS', 'CAR', 'CHI', 'CIN', 'DEN', 'PHI', 'DET', 'PIT', 'TEN', 'KC', 'NE', 'TB', 'ATL', 'DAL', 'HOU', 'SEA', 'GB', 'NYG', 'ARI', 'IND', 'SF', 'BUF', 'LAC', 'OAK', 'NO']

# return teamID function without DB
def getTeamID(teamName):
    teamIndex = teamNameLookup.index(teamName)
    return teamIDLookup[teamIndex]

# return teamName function without DB
def getTeamName(teamID):
    teamIndex = teamIDLookup.index(teamID)
    return teamNameLookup[teamIndex]

# class object blueprint
class Matchup:
  def __init__(self, matchupKey, teamID, teamName, passYards, rushYards, totalYards):
    self.matchupKey = matchupKey
    self.teamID = teamID
    self.teamName = teamName
    self.rushYards = rushYards
    self.passYards = passYards
    self.totalYards = totalYards

def getFantasyPoints(matchup,week,team):
    # call the getStats function for the selected team and week
    stats = getStats(matchup,week,team,'Sack','Int','Saf','FR','Blk','TD','PA','TotYds')
    if stats == "BYE":
        return stats
    else:
        # calc tier for ptsAllowed
        pointsPA = 0
        if stats[6] == 0: pointsPA = 5
        elif 1 <= stats[6] <= 6: pointsPA = 4
        elif 7 <= stats[6] <= 13: pointsPA = 3
        elif 14 <= stats[6] <= 17: pointsPA = 1
        elif 18 <= stats[6] <= 27: pointsPA = 0
        elif 28 <= stats[6] <= 34: pointsPA = -1
        elif 35 <= stats[6] <= 45: pointsPA = -3
        elif 46 <= stats[6]: pointsPA = -5
        # calc tier for ydsAllowed
        pointsYA = 0
        if stats[7] < 100: pointsYA = 5
        elif 100 <= stats[7] <= 199: pointsYA = 3
        elif 200 <= stats[7] <= 299: pointsYA = 2
        elif 300 <= stats[7] <= 399: pointsYA = -1
        elif 400 <= stats[7] <= 449: pointsYA = -3
        elif 450 <= stats[7] <= 499: pointsYA = -5
        elif 500 <= stats[7] <= 549: pointsYA = -6
        elif 550 <= stats[7]: pointsYA = -7

        # calculate the points
        fantasyPoints = stats[0]*1 + stats[1]*2 + stats[2]*2 + stats[3]*2 + stats[4]*2 + stats[5]*6 + pointsPA + pointsYA
        return fantasyPoints

def getAvgDefPts(teamName):
    weekCount = 0
    totalPoints = 0
    pointsArray = []
    for week in range(1,18):
        weekPoints = getFantasyPoints(False,week,teamName)
        if weekPoints != "BYE":
            weekCount += 1
            totalPoints += weekPoints
            pointsArray.append(weekPoints)
    pointsArray.append(round(totalPoints/weekCount,2))
    return pointsArray

def getAvgStat(matchup,teamName,stat):
    weekCount = 0
    totalStat = 0
    statArray = []
    for week in range(1,18):
        weekStat = getStats(matchup,week,teamName,stat)[0]
        if weekStat != "B":
            weekCount += 1
            totalStat += float(weekStat)
            statArray.append(weekStat)
    statArray.append(round(totalStat/weekCount,2))
    return statArray

def getStats(matchup,week,teamName,*argv): # matchup T/F - True is opposing team stats

    # instance variables
    stats = []

    # The url we will be scraping
    boxscore = "https://www.footballdb.com/fantasy-football/index.html?pos=DST&yr=2018&wk=" + str(week) +"&rules=1"

    # get the html
    html = urlopen(boxscore)

    # create the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # collect team rows
    teamRow = None
    teamRows = soup.find(class_='statistics scrollable').find('tbody').findAll('tr')

    # main team or matchup team
    if matchup == True:
        # get the teamID
        teamID = getTeamID(teamName) # get the ID from the db

        # find the correct team row based on MATCHUP name
        for team in teamRows:
            matchupID = team.findAll('td')[1].getText()
            matchupID = matchupID[-int(len(matchupID)-matchupID.rfind(" ")-1):]
            if matchupID == teamID:
                teamRow = team
    else:
         # find the correct team row based on NON MATCHUP name
        for team in teamRows:
            rowName = team.findAll('td')[0].find('a').getText()
            if rowName == teamName:
                teamRow = team
                
    # check if team was not found and therefor on bye
    if teamRow == None:
        return "BYE"
    # loop through the variable stat arguments
    for stat in argv:
        # find the correct stat column
        statIndex = 0
        statsHeader = soup.find(class_='statistics scrollable').findAll('thead')[0]
        statIndex = statsHeader.findAll('th').index(statsHeader.find('th',string=stat))
        # combine the coordinates
        stats.append(float(teamRow.findAll('td')[statIndex].getText()))
    return stats

def storeAllStatsDST(week):
    # database connection
    mydb = MySQLdb.connect(
        host='192.168.1.251', #host='35.231.120.222', 
        user='root', 
        passwd='root',
        db='nflStats'
    )
    
    # The url we will be scraping
    boxscore = "https://www.footballdb.com/fantasy-football/index.html?pos=DST&yr=2018&wk=" + str(week) +"&rules=1"

    # get the html
    html = urlopen(boxscore)

    # create the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # collect team rows
    teamRow = None
    teamRows = soup.find(class_='statistics scrollable').find('tbody').findAll('tr')

    # byeCheckArray
    byeCheckArray = []

    for team in teamRows:
        # team name
        teamName = str(team.findAll('td')[0].find('a').getText())
        # team week ID
        teamID = getTeamID(teamName) + str(week)
        byeCheckArray.append(getTeamID(teamName))
        # matchup team week ID
        matchupID = team.findAll('td')[1].getText()
        matchupID = matchupID[-int(len(matchupID)-matchupID.rfind(" ")-1):] + str(week)
        #bye week
        bye=False
        # home team
        location = team.findAll('td')[1].getText()
        if location.find('@') != -1:
            home = True
        else:
            home = False
        # sack
        sacks = team.findAll('td')[3].getText()
        # int
        inters = team.findAll('td')[4].getText()
        # saf
        safties = team.findAll('td')[5].getText()
        # FR
        fumRecs = team.findAll('td')[6].getText()
        # Blk
        blocks = team.findAll('td')[7].getText()
        # TD
        tds = team.findAll('td')[8].getText()
        # PA
        ptsAllowed = team.findAll('td')[9].getText()
        # PassYds
        passYdsAllowed = team.findAll('td')[10].getText()
        # RushYds
        rushYdsAllowed = team.findAll('td')[11].getText()
        # TotYds
        totYdsAllowed = team.findAll('td')[12].getText()

        # get TeamID from DB ####### ADD MORE IN THE ON DUP %s %s %s for all values to overwrite
        sql = "INSERT INTO dstStats VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE matchupID=%s, byeWeek=%s, home=%s, sack=%s, inter=%s, safety=%s, fumRec=%s, block=%s, touchdown=%s, ptsAllowed=%s, passYdsAllowed=%s, rushYdsAllowed=%s, totalYdsAllowed=%s"
        val = (teamID, matchupID, teamName, bye, home, sacks, inters, safties, fumRecs, blocks, tds, ptsAllowed, passYdsAllowed, rushYdsAllowed, totYdsAllowed, matchupID, bye, home, sacks, inters, safties, fumRecs, blocks, tds, ptsAllowed, passYdsAllowed, rushYdsAllowed, totYdsAllowed)
        mycursor = mydb.cursor()
        mycursor.execute(sql, val)
        mydb.commit()
        
    # check if team was not found and therefor on bye
    for teamID in teamIDLookup:
        try:
            index = byeCheckArray.index(teamID)
        except:
            index = -1
        if index == -1:
             # team must be on bye
            gameID = teamID + str(week)
            print("BYE WEEK: " + teamID)
            teamName = getTeamName(teamID)
            sql = "INSERT INTO dstStats(gameID,matchupID,team,byeWeek) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE matchupID=%s"
            val = (gameID, "BYE", teamName, True, "BYE")
            mycursor = mydb.cursor()
            mycursor.execute(sql, val)
            mydb.commit()

# predict stat for teamA

storeAllStatsDST(2)
storeAllStatsDST(3)
storeAllStatsDST(4)
storeAllStatsDST(5)
storeAllStatsDST(6)
storeAllStatsDST(7)
storeAllStatsDST(8)