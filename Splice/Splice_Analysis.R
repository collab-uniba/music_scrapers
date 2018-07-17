require(foreach)
library(corrplot)

options(digits = 3)

authors <- read.csv("Data/SpliceAuthors.csv",sep = ";")
songs <- read.csv("Data/SpliceSongs.csv", sep = ";")

data <- merge(songs, authors, by.x = "Author", by.y = "Username")
data$Co.Author <- ifelse(data$Co.Author!="-",TRUE,FALSE)
data$Released.Splices <- ifelse(data$Released.Splices>0,TRUE,FALSE)

data$DateDiff <- foreach(i=1:length(data$Date)) %do% difftime(strptime("31/01/2018", format = "%d/%m/%Y"), strptime(data$Date[i], format = "%d/%m/%Y"),units="days")
data$JoinDateDiff <- foreach(i=1:length(data$SignUp.Date)) %do% difftime(strptime("31/01/2018", format = "%d/%m/%Y"), strptime(data$SignUp.Date[i], format = "%d/%m/%Y"),units="days")

data <- within(data,{
  IsSpliced <- as.logical(IsSpliced) 
  Co.Author <- as.logical(Co.Author)
  Plays <- as.numeric(Plays) 
  Splices <- as.numeric(Splices)
  Released.Splices <- as.logical(Released.Splices) 
  Likes <- as.numeric(Likes)
  Comments <- as.numeric(Comments)
  DateDiff <- as.numeric(DateDiff)
  
  AuthorPlays <- as.numeric(AuthorPlays) 
  AuthorLikes <- as.numeric(AuthorLikes) 
  Followers <- as.numeric(Followers) 
  Releases <- as.numeric(Releases) 
  JoinDateDiff <- as.numeric(JoinDateDiff)
  HasBio <- as.logical(HasBio) 
  AuthorRank <- as.numeric((AuthorPlays+AuthorLikes+Followers)/(Releases+JoinDateDiff))
})

data$Plays <- log1p(data$Plays)
data$Splices <- log1p(data$Splices)
data$Likes <- log1p(data$Likes)
data$Comments <- log1p(data$Comments)
data$DateDiff <- log1p(data$DateDiff)#
data$AuthorPlays <- log1p(data$AuthorPlays)
data$AuthorLikes <- log1p(data$AuthorLikes)
data$Followers <- log1p(data$Followers)
data$Releases <- log1p(data$Releases)#
data$AuthorRank <- log1p(data$AuthorRank)

data$Plays <- scale(data$Plays, center= TRUE, scale=TRUE)
data$Splices <- scale(data$Splices, center= TRUE, scale=TRUE)
data$Likes <- scale(data$Likes, center= TRUE, scale=TRUE)
data$Comments <- scale(data$Comments, center= TRUE, scale=TRUE)
data$DateDiff <- scale(data$DateDiff, center= TRUE, scale=TRUE)#
data$AuthorPlays <- scale(data$AuthorPlays, center= TRUE, scale=TRUE)
data$AuthorLikes <- scale(data$AuthorLikes, center= TRUE, scale=TRUE)
data$Followers <- scale(data$Followers, center= TRUE, scale=TRUE)
data$Releases <- scale(data$Releases, center= TRUE, scale=TRUE)#
data$AuthorRank <- scale(data$AuthorRank, center= TRUE, scale=TRUE)

model1 <- glm(data$Released.Splices~ 
                # song level
                Likes +
                Comments +
                DateDiff +
                IsSpliced +
                # author level
                Followers +
                AuthorRank
                , 
              data = data,
              family = binomial(link = "logit")
)
AIC(model1)
round(exp(cbind(odds=coef(model1), confint(model1, method="Wald", level = 0.99))), 3)
car::Anova(model1)
sjstats::r2(model1) # Nagelkerke adjusted R2
car::vif(model1)


library(ROCR)
require(caret)

set.seed(123)
trainIndex <- createDataPartition(data$Released.Splices, p = .7,  list = FALSE, times = 1)
lmm.data.train <- data[ trainIndex,]
lmm.data.test  <- data[-trainIndex,]

mp1 <- predict(model1, newdata=lmm.data.test, type="response")
mpr <- prediction(mp1, lmm.data.test$Released.Splices)
mprf <- performance(mpr, measure = "tpr", x.measure = "fpr")
plot(mprf)
auc <- performance(mpr, measure = "auc")
auc <- auc@y.values[[1]]
auc

