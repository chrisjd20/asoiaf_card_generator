# asoiaf_card_generator
takes cmon data to generate asoiaf cards. 

Builds the front side of the:
* Attachments
* NCUS
* Tactics
* Specials
* Combat Unis


If you want to build, be in the `flutter_assets` folder and run:

```
pip3 install pillow boto3 
python3 download_csvs.py
```

Then to generate german cards:

```
python3 ncu_card_generator.py de && python3 unit_card_generator.py de && python3 tactics_card_generator.py de && python3 special_card_generator.py de && python3 attachment_card_generator.py de
```

I only tested this on `de`, `fr`, and `en`. 

Credit for tactics cards creation goes to Pf2eTools over at:

https://github.com/Pf2eTools/asoiaf_card_generator/tree/main

Although I tweaked what he started with so his stuff will probably better than mine in the long run once he finishes. 
