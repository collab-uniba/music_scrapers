library(foreach)
library(corrplot)

options(digits = 3)

authors <- read.csv("Data/CCMixterAuthorsAPIlist.csv", stringsAsFactors = FALSE)
songs <- read.csv("Data/CCMixterSongsAPIlist.csv", stringsAsFactors = FALSE)
data <- merge(songs, authors, by.x = "Author", by.y = "Username")#, all.x = TRUE
contestsOnly <- read.csv("Data/contestsOnly.csv", sep = ";", stringsAsFactors = FALSE)

valid <- data[!data$Title %in% contestsOnly$upload_name,]
mergedToVerify <- merge(valid, contestsOnly, by.x = "Title", by.y = "upload_name", all.x = TRUE)#, all.x = TRUE

data <- valid

data$featuring <- ifelse(data$featuring!="-",TRUE,FALSE)
data$samplesFrom <- ifelse(data$samplesFrom!="-",TRUE,FALSE)
data$samplesIn <- ifelse(data$samplesIn!="-",TRUE,FALSE)
data$DateDiff <- foreach(i=1:length(data$dateUpload)) %do% difftime(strptime("28/02/2018", format = "%d/%m/%Y"), strptime(data$dateUpload[i], format = "%b %d, %Y %H:%M"),units="days")
data$JoinDateDiff <- foreach(i=1:length(data$SignUpDate)) %do% difftime(strptime("28/02/2018", format = "%d/%m/%Y"), strptime(data$SignUpDate[i], format = "%b %d, %Y "),units="days")
data$Uploads <- ifelse(data$Uploads==0,1,data$Uploads)

data1 <- within(data,{
  samplesFrom <- as.logical(samplesFrom)
  samplesIn <- as.logical(samplesIn)
  featuring <- as.logical(featuring) 
  recommends <- as.numeric(recommends) 
  reviews <- as.numeric(reviews)
  
  Uploads <- as.numeric(Uploads)
  HasAvatar <- as.logical(HasAvatar) 
  remixDone <- as.numeric(remixDone)
  remixReceived <- as.numeric(remixReceived)
  PlaylistsWithAuthor <- as.numeric(PlaylistsWithAuthor)
  forumMessage <- as.numeric(forumMessage)
  reviewLeft <- as.numeric(reviewLeft)
  reviewReceived <- as.numeric(reviewReceived)
  DateDiff <- as.numeric(DateDiff)
  JoinDateDiff <- as.numeric(JoinDateDiff)
  AuthorRank <- as.numeric((remixReceived + PlaylistsWithAuthor + reviewReceived)/(Uploads+remixDone+reviewLeft))
})

data1$recommends <- log1p(data1$recommends)
data1$reviews <- log1p(data1$reviews)
data1$PlaylistsWithAuthor <- log1p(data1$PlaylistsWithAuthor)
data1$DateDiff <- log1p(data1$DateDiff)
data1$AuthorRank <- log1p(data1$AuthorRank)

data1$recommends <- scale(data1$recommends, center= TRUE, scale=TRUE)
data1$reviews <- scale(data1$reviews, center= TRUE, scale=TRUE)
data1$PlaylistsWithAuthor <- scale(data1$PlaylistsWithAuthor, center= TRUE, scale=TRUE)
data1$DateDiff <- scale(data1$DateDiff, center= TRUE, scale=TRUE)
data1$AuthorRank <- scale(data1$AuthorRank, center= TRUE, scale=TRUE)

model1 <- glm(data1$samplesIn ~ 
                # song level
                recommends +
                reviews +
                DateDiff + 
                samplesFrom +
                
                # author level
                AuthorRank +
                HasAvatar
              , 
              data = data1,
              family = binomial(link = "logit")
)
AIC(model1)
round(exp(cbind(odds=coef(model1), confint(model1, method="Wald", level = 0.99))) , 3)
car::Anova(model1)
sjstats::r2(model1) # Nagelkerke adjusted R2
car::vif(model1)


library(ROCR)
require(caret)

set.seed(123)
trainIndex <- createDataPartition(data$samplesIn, p = .7,  list = FALSE, times = 1)
lmm.data.train <- data1[ trainIndex,]
lmm.data.test  <- data1[-trainIndex,]

mp1 <- predict(model1, newdata=lmm.data.test, type="response")
mpr <- prediction(mp1, lmm.data.test$samplesIn)
mprf <- performance(mpr, measure = "tpr", x.measure = "fpr")
plot(mprf)
auc <- performance(mpr, measure = "auc")
auc <- auc@y.values[[1]]
auc
