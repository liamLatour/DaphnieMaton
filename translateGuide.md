# How to help by translating

- Install [Poedit](https://poedit.net/)
- Go to Code/app/assets/libraries/localization/translations
- Open the .pot file with poedit
- Create your translation in the language you want
- When done save to the same folder following this pattern: ./translations/*language code*/LC_MESSAGES/*save here*
for example ./translations/en/LC_MESSAGES
- Update the ./translations/Language/LC_MESSAGES/languages.po file with the conversion from the language code to it's real name
- git commit -> git push
- That's all, the language will be added in the next version !
