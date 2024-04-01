#!/bin/bash


source ./.venv/bin/activate 

cd ~/Bureau/crawler/crawler 


listAll=$(scrapy list) 

forbid=(creteil agen bastia besancon bourg)


for item in ${listAll[@]}; do
  if  ! [[ " ${forbid[@]} " =~ " ${item} " ]]; then
    echo $item
    scrapy crawl $item -O "$item.csv"
  fi
done