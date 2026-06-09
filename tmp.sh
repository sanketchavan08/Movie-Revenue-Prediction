/^\* [0-9]+ FETCH/ {
  if (msg)
    printf "%s\t%s\t%s\t%s\t%s\n",from,to,subj,size,date
  msg=$2; from=""; to=""; subj=""; size=""; date=""
  if (match($0,/RFC822\.SIZE [0-9]+/)) {
    s=substr($0,RSTART+12,RLENGTH-12)
    size=sprintf("%.1f",s/1024)
  }
  if (match($0,/INTERNALDATE "[^"]+"/))
    date=substr($0,RSTART+13,RLENGTH-14)
}
/^From:/ { sub(/^From: */,""); from=$0 }
/^To:/ { sub(/^To: */,""); to=$0 }
/^Subject:/ { sub(/^Subject: */,""); subj=$0 }
END {
  if (msg)
    printf "%s\t%s\t%s\t%s\t%s\n",from,to,subj,size,date
}
