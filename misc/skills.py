import discord
import re


async def skill_name_search(text_field_1):
    search_pattern_skill_name = r"\*\*(.*?)\*\*"
    skill_name_search = re.findall(search_pattern_skill_name, text_field_1)
    skill_name = skill_name_search[0]
    if skill_name == "Lucky Coin":
        skill_text_base = text_field_1.replace("<:LUCKY_COIN:723700092594552913>", "<:LUCKY_COIN:1335616797449125888>")
        skill_text_sr = skill_text_base.replace("a __20__ sided", "a __36__ sided")
        skill_text_ur = skill_text_base.replace("a __20__ sided", "a __40__ sided")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Amplifier":
        skill_text_base = text_field_1.replace("<:AMPLIFIER:704094158700150904>", "<:AMPLIFIER:1335617081013440573>")
        skill_text_sr = skill_text_base.replace("allied familiars by __14__%", "allied familiars by __25__%")
        skill_text_ur = skill_text_base.replace("allied familiars by __14__%", "allied familiars by __28__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Arcane Affinity":
        skill_text_base = text_field_1.replace("<:ARCANE_AFFINITY:1293458242260697119>", "<:Arcane_Affinity:1335617073505636372>")
        skill_text_sr = skill_text_base.replace("this battle by __17__%", "this battle by __30__%")
        skill_text_ur = skill_text_base.replace("this battle by __17__%", "this battle by __34__%")
        skill_text_sr = skill_text_sr.replace("deal __3__% of the", "deal __5__% of the")
        skill_text_ur = skill_text_ur.replace("deal __3__% of the", "deal __6__% of the")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Balancing Strike":
        skill_text_base = text_field_1.replace("<:BALANCING_STRIKE:708452835632742482>", "<:Balancing_Strike:1335617062390992996>")
        skill_text_sr = skill_text_base.replace("HP %, deal __15__% of", "HP %, deal __27__% of")
        skill_text_ur = skill_text_base.replace("HP %, deal __15__% of", "HP %, deal __30__% of")
        skill_text_sr = skill_text_sr.replace("this skill deals __5__%", "this skill deals __9__% of your")
        skill_text_ur = skill_text_ur.replace("this skill deals __5__%", "this skill deals __10__% of your")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Berserker":
        skill_text_base = text_field_1.replace("<:BERSERKER:704097914347192370>", "<:Berserker:1335617052987097189>")
        skill_text_sr = skill_text_base.replace("familiars by __30__%", "familiars by __54__%")
        skill_text_ur = skill_text_base.replace("familiars by __30__%", "familiars by __60__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Blaze":
        skill_text_base = text_field_1.replace("<:BURN:704096180224655370>", "<:Blaze:1335617044372000860>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Blood Surge":
        skill_text_base = text_field_1.replace("<:BLOOD_SURGE:708452836215619584>", "<:Blood_Surge:1335617034632953949>")
        skill_text_sr = skill_text_base.replace("allies by __45__%", "allies by __81__%")
        skill_text_ur = skill_text_base.replace("allies by __45__%", "allies by __90__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Bloodthirster":
        skill_text_base = text_field_1.replace("<:BLOODTHIRSTER:708452836232396850>", "<:Bloodthirster:1335617024134610944>")
        skill_text_sr = skill_text_base.replace("HP equal to __18__%", "HP equal to __32__%")
        skill_text_ur = skill_text_base.replace("HP equal to __18__%", "HP equal to __36__%")
        skill_text_sr = skill_text_sr.replace("healing effects by __23__%", "healing effects by __41__%")
        skill_text_ur = skill_text_ur.replace("healing effects by __23__%", "healing effects by __46__%")
        skill_text_sr = skill_text_sr.replace("LIFESTEAL by __4__%", "LIFESTEAL by __7__%")
        skill_text_ur = skill_text_ur.replace("LIFESTEAL by __4__%", "LIFESTEAL by __8__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Breaker":
        skill_text_base = text_field_1.replace("<:BREAKER:704168490893967441>", "<:Breaker:1335617008133214238>")
        skill_text_sr = skill_text_base.replace("familiars by __20__%", "familiars by __36__%")
        skill_text_ur = skill_text_base.replace("familiars by __20__%", "familiars by __40__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Brutality":
        skill_text_base = text_field_1.replace("<:BRUTALITY:1311197053317156874>", "<:Brutality:1335616998968791041>")
        skill_text_sr = skill_text_base.replace("storing __33__%", "storing __59__%")
        skill_text_ur = skill_text_base.replace("storing __33__%", "storing __66__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Celestial Blessing":
        skill_text_base = text_field_1.replace("<:CELESTIAL_BLESSING:839596829645340684>", "<:Celestial_Blessing:1335616987967127684>")
        skill_text_sr = skill_text_base.replace("Regeneration by __18__%", "Regeneration by __32__%")
        skill_text_ur = skill_text_base.replace("Regeneration by __18__%", "Regeneration by __36__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Celestial Influence":
        skill_text_base = text_field_1.replace("<:CELESTIAL_INFLUENCE:723700092942417971>", "<:Celestial_Influence:1335616977707733084>")
        skill_text_sr = skill_text_base.replace("battle with __40__%", "battle with __72__%")
        skill_text_ur = skill_text_base.replace("battle with __40__%", "battle with __80__%")
        skill_text_sr = skill_text_sr.replace("Mana Regen by __14__%", "Mana Regen by __25__%")
        skill_text_ur = skill_text_ur.replace("Mana Regen by __14__%", "Mana Regen by __28__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Cursed":
        skill_text_base = text_field_1.replace("<:CURSED:1252439442342285323>", "<:Cursed:1335616960129531964>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Devour":
        skill_text_base = text_field_1.replace("<:DEVOUR:1068219756093644800>", "<:Devour:1335616950264401993>")
        skill_text_sr = skill_text_base.replace("Deal __5__% of max", "Deal __9__% of max")
        skill_text_ur = skill_text_base.replace("Deal __5__% of max", "Deal __10__% of max")
        skill_text_sr = skill_text_sr.replace("base HP by __8__%", "base HP by __14__%")
        skill_text_ur = skill_text_ur.replace("base HP by __8__%", "base HP by __16__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Dexterity Drive":
        skill_text_base = text_field_1.replace("<:DEXTERITY_DRIVE:706653721441861663>", "<:Dexterity_Drive:1335616941380993105>")
        skill_text_sr = skill_text_base.replace("equal to __5__%", "equal to __9__%")
        skill_text_ur = skill_text_base.replace("equal to __5__%", "equal to __10__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Divine Blessing":
        skill_text_base = text_field_1.replace("<:DIVINE_BLESSING:708452836328996864>", "<:Divine_Blessing:1335616933323608125>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Dominance":
        skill_text_base = text_field_1.replace("<:DOMINANCE:715770410217635840>", "<:Dominance:1335616923668451368>")
        skill_text_sr = skill_text_base.replace("allies by __17__%", "allies by __30__%")
        skill_text_ur = skill_text_base.replace("allies by __17__%", "allies by __34__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Double-edged Strike":
        skill_text_base = text_field_1.replace("<:DOUBLE_EDGED_STRIKE:708452836819861574>", "<:Double_edged_Strike:1335616913484677231>")
        skill_text_sr = skill_text_base.replace("to __15__% of your", "to __27__% of your")
        skill_text_ur = skill_text_base.replace("to __15__% of your", "to __30__% of your")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Elemental Drain":
        skill_text_base = text_field_1.replace("<:ELEMENTAL_DRAIN:1333722965119864872>", "<:Elemental_Drain:1335616903913275433>")
        skill_text_sr = skill_text_base.replace("equal to __5__%", "equal to __9__%")
        skill_text_ur = skill_text_base.replace("equal to __5__%", "equal to __10__%")
        skill_text_sr = skill_text_sr.replace("plus __3__% for", "plus __5__% for")
        skill_text_ur = skill_text_ur.replace("plus __3__% for", "plus __6__% for")
        skill_text_sr = skill_text_sr.replace("heal for __20__%", "heal for __36__%")
        skill_text_ur = skill_text_ur.replace("heal for __20__%", "heal for __40__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Elemental Manipulation":
        skill_text_base = text_field_1.replace("<:ELEMENTAL_MANIPULATION:1242689424924606494>", "<:Elemental_Manipulation:1335616891623837697>")
        skill_text_sr = skill_text_base.replace("DMG dealt by __3__%", "DMG dealt by __5__%")
        skill_text_ur = skill_text_base.replace("DMG dealt by __3__%", "DMG dealt by __6__%")
        skill_text_sr = skill_text_sr.replace("heals yourself for __2__%", "heals yourself for __3__%")
        skill_text_ur = skill_text_ur.replace("heals yourself for __2__%", "heals yourself for __4__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Elemental Strike":
        skill_text_base = text_field_1.replace("<:METEOR:704094159136620675>", "<:Elemental_Strike:1335616878931873822>")
        skill_text_sr = skill_text_base.replace("based on __10__%", "based on __18__%")
        skill_text_ur = skill_text_base.replace("based on __10__%", "based on __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Endurance":
        skill_text_base = text_field_1.replace("<:ENDURANCE:736144385422524416>", "<:Endurance:1335616869138169856>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Evasion":
        skill_text_base = text_field_1.replace("<:EVASION:706654671367831602>", "<:Evasion:1335616859592196149>")
        skill_text_sr = skill_text_base.replace("EVASION by __17__%", "EVASION by __30__%")
        skill_text_ur = skill_text_base.replace("EVASION by __17__%", "EVASION by __34__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Executioner":
        skill_text_base = text_field_1.replace("<:EXECUTIONER:708452836190584913>", "<:Executioner:1335616849299378257>")
        skill_text_sr = skill_text_base.replace("health is below __27__%", "health is below __48__%")
        skill_text_ur = skill_text_base.replace("health is below __27__%", "health is below __54__%")
        skill_text_sr = skill_text_sr.replace("your ATK by __50__%", "your ATK by __90__%")
        skill_text_ur = skill_text_ur.replace("your ATK by __50__%", "your ATK by __100__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Foul Play":
        skill_text_base = text_field_1.replace("<:FOUL_PLAY:1308972889734643722>", "<:Foul_Play:1335616838549110856>")
        skill_text_sr = skill_text_base.replace("stats by __22__%", "stats by __39__%")
        skill_text_ur = skill_text_base.replace("stats by __22__%", "stats by __44__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Freeze":
        skill_text_base = text_field_1.replace("<:FROZEN:704094159157329991>", "<:Freeze:1335616828399026260>")
        skill_text_sr = skill_text_base.replace("by __10__%", "by __18__%")
        skill_text_ur = skill_text_base.replace("by __10__%", "by __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Vengeance":
        skill_text_base = text_field_1.replace("<:VENGEANCE:704094159274901645>", "<:Vengeance:1335616408347873283>")
        skill_text_sr = skill_text_base.replace("to __11__%", "to __19__%")
        skill_text_ur = skill_text_base.replace("to __11__%", "to __22__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Yin Yang":
        skill_text_base = text_field_1.replace("<:YIN_YANG:1193159288424771615>", "<:Yin_Yang:1335616388567531661>")
        skill_text_sr = skill_text_base.replace("healing all allies by __4__%", "healing all allies by __7__%")
        skill_text_ur = skill_text_base.replace("healing all allies by __4__%", "healing all allies by __8__%")
        skill_text_sr = skill_text_sr.replace("your ATK and SPD by __5__%", "your ATK and SPD by __9__%")
        skill_text_ur = skill_text_ur.replace("your ATK and SPD by __5__%", "your ATK and SPD by __10__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Offensive Stance":
        skill_text_base = text_field_1.replace("<:OFFENSIVE_STANCE:708760406088351874>", "<:Offensive_Stance:1335616767300468846>")
        skill_text_sr = skill_text_base.replace("familiars by __40__%", "familiars by __72__%")
        skill_text_ur = skill_text_base.replace("familiars by __40__%", "familiars by __80__%")
        skill_text_sr = skill_text_sr.replace("their DEF by __10__%", "their DEF by __18__%")
        skill_text_ur = skill_text_ur.replace("their DEF by __10__%", "their DEF by __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Overload":
        skill_text_base = text_field_1.replace("<:OVERLOAD:708760380327067759>", "<:Overload:1335616751752450129>")
        skill_text_sr = skill_text_base.replace("by __55__%", "by __99__%")
        skill_text_ur = skill_text_base.replace("by __55__%", "by __110__%")
        skill_text_sr = skill_text_sr.replace("decreases by __8__%", "decreases by __14__%")
        skill_text_ur = skill_text_ur.replace("decreases by __8__%", "decreases by __16__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Pain For Power":
        skill_text_base = text_field_1.replace("<:PAIN_FOR_POWER:736792609090961461>", "<:Pain_For_Power:1335616736866734222>")
        skill_text_sr = skill_text_base.replace("Sacrifice __7__%", "Sacrifice __12__%")
        skill_text_ur = skill_text_base.replace("Sacrifice __7__%", "Sacrifice __14__%")
        skill_text_sr = skill_text_sr.replace("familiars by __30__%", "familiars by __54__%")
        skill_text_ur = skill_text_ur.replace("familiars by __30__%", "familiars by __60__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Paralysis":
        skill_text_base = text_field_1.replace("<:PARALYSIS:704094159082094602>", "<:Paralysis:1335616727312109589>")
        skill_text_sr = skill_text_base.replace("Gain a __40__% chance", "Gain a __72__% chance")
        skill_text_ur = skill_text_base.replace("Gain a __40__% chance", "Gain a __80__% chance")
        skill_text_sr = skill_text_sr.replace("their DEF by __10__%", "their DEF by __18__%")
        skill_text_ur = skill_text_ur.replace("their DEF by __10__%", "their DEF by __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Poison":
        skill_text_base = text_field_1.replace("<:POISON:704094158880768041>", "<:Poison:1335616714322477177>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Precision":
        skill_text_base = text_field_1.replace("<:PRECISION:704094159295741973>", "<:Precision:1335616702712381520>")
        skill_text_sr = skill_text_base.replace("familiars by __16__%", "familiars by __28__%")
        skill_text_ur = skill_text_base.replace("familiars by __16__%", "familiars by __32__%")
        skill_text_sr = skill_text_sr.replace("DMG by __25__%", "DMG by __45__%")
        skill_text_ur = skill_text_ur.replace("DMG by __25__%", "DMG by __50__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Protector":
        skill_text_base = text_field_1.replace("<:PROTECTOR:704099854413987860>", "<:Protector:1335616686140686469>")
        skill_text_sr = skill_text_base.replace("familiars by __20__%", "familiars by __36__%")
        skill_text_ur = skill_text_base.replace("familiars by __20__%", "familiars by __40__%")
        skill_text_sr = skill_text_sr.replace("DEF by __35__%", "DEF by __63__%")
        skill_text_ur = skill_text_ur.replace("DEF by __35__%", "DEF by __70__%")
        skill_text_sr = skill_text_sr.replace("damage taken by __5__%", "damage taken by __9__%")
        skill_text_ur = skill_text_ur.replace("damage taken by __5__%", "damage taken by __10__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Recoil":
        skill_text_base = text_field_1.replace("<:RECOIL:704100508398387260>", "<:Recoil:1335616675046752348>")
        skill_text_sr = skill_text_base.replace("familiars by __15__%", "familiars by __27__%")
        skill_text_ur = skill_text_base.replace("familiars by __15__%", "familiars by __30__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Life Sap":
        skill_text_base = text_field_1.replace("<:LIFE_SAP:753838218293543022>", "<:Life_Sap:1335616663382528091>")
        skill_text_sr = skill_text_base.replace("deal __2__%", "deal __3__%")
        skill_text_ur = skill_text_base.replace("deal __2__%", "deal __4__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Reflector":
        skill_text_base = text_field_1.replace("<:REFLECTOR:902491425176952843>", "<:Reflector:1335616644092919879>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Regeneration":
        skill_text_base = text_field_1.replace("<:REGENERATION:704097888799817789>", "<:Regeneration:1335616631774249032>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Rejuvenation":
        skill_text_base = text_field_1.replace("<:REJUVENATION:704094157836124211>", "<:Rejuvenation:1335616621724831876>")
        skill_text_sr = skill_text_base.replace("all allied familiars by __12__%", "all allied familiars by __21__%")
        skill_text_ur = skill_text_base.replace("all allied familiars by __12__%", "all allied familiars by __24__%")
        skill_text_sr = skill_text_sr.replace("healing effects on allied familiars by __10__%", "healing effects on allied familiars by __18__%")
        skill_text_ur = skill_text_ur.replace("healing effects on allied familiars by __10__%", "healing effects on allied familiars by __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Restricted Instinct":
        skill_text_base = text_field_1.replace("<:SILENCE:723700093299064852>", "<:Restricted_Instinct:1335616611045998705>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Reversion":
        skill_text_base = text_field_1.replace("<:REVERSION:768758421863661578>", "<:Reversion:1335616600602316881>")
        skill_text_sr = skill_text_base.replace("health drops below __20__%", "health drops below __36__%")
        skill_text_ur = skill_text_base.replace("health drops below __20__%", "health drops below __40__%")
        skill_text_sr = skill_text_sr.replace("their DEF/SPD by __12__%", "their DEF/SPD by __21__%")
        skill_text_ur = skill_text_ur.replace("their DEF/SPD by __12__%", "their DEF/SPD by __24__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Rising Resolve":
        skill_text_base = text_field_1.replace("<:RISING_RESOLVE:1300560038468911205>", "<:Rising_Resolve:1335616590577926225>")
        skill_text_sr = skill_text_base.replace("your stats by __8__%", "your stats by __14__%")
        skill_text_ur = skill_text_base.replace("your stats by __8__%", "your stats by __16__%")
        skill_text_sr = skill_text_sr.replace("restore __10__%", "restore __18__%")
        skill_text_ur = skill_text_ur.replace("restore __10__%", "restore __20__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Smokescreen":
        skill_text_base = text_field_1.replace("<:SMOKESCREEN:1083565284843069530>", "<:Smokescreen:1335616580318658592>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Soul Stealer":
        skill_text_base = text_field_1.replace("<:SOUL_STEALER:798404124575137813>", "<:Soul_Stealer:1335616569694359603>")
        skill_text_sr = skill_text_base.replace("Absorb __4__%", "Absorb __7__%")
        skill_text_ur = skill_text_base.replace("Absorb __4__%", "Absorb __8__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Temporal Rewind":
        skill_text_base = text_field_1.replace("<:TEMPORAL_REWIND:732111441133568002>", "<:Temporal_Rewind:1335616556058804255>")
        skill_text_sr = skill_text_base
        skill_text_ur = skill_text_base
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Time Attack":
        skill_text_base = text_field_1.replace("<:TIME_ATTACK:723700093139812381>", "<:Time_Attack:1335616536542576671>")
        skill_text_sr = skill_text_base.replace("Deal __5__%", "Deal __9__%")
        skill_text_ur = skill_text_base.replace("Deal __5__%", "Deal __10__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Time Bomb":
        skill_text_base = text_field_1.replace("<:TIME_BOMB:723700093236019300>", "<:Time_Bomb:1335616525352308839>")
        skill_text_sr = skill_text_base.replace("damage taken by __7__%", "damage taken by __12__%")
        skill_text_ur = skill_text_base.replace("damage taken by __7__%", "damage taken by __14__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Trick Room":
        skill_text_base = text_field_1.replace("<:TRICK_ROOM:715770429012312094>", "<:Trick_Room:1335616485900554321>")
        skill_text_sr = skill_text_base.replace("equal to __60__%", "equal to __108__%")
        skill_text_ur = skill_text_base.replace("equal to __60__%", "equal to __120__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Transformation":
        skill_text_base = text_field_1.replace("<:TRANSFORMATION:736144385221197864>", "<:Transformation:1335616512152567901>")
        skill_text_sr = skill_text_base.replace("familiars by __15__%,", "familiars by __27__%,")
        skill_text_ur = skill_text_base.replace("familiars by __15__%,", "familiars by __30__%,")
        skill_text_sr = skill_text_sr.replace("by __30__%.", "by __54__%.")
        skill_text_ur = skill_text_ur.replace("by __30__%.", "by __60__%.")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Ultimate Combo":
        skill_text_base = text_field_1.replace("<:ULTIMATE_COMBO:736144384910688266>", "<:Ultimate_Combo:1335616472709333023>")
        skill_text_sr = skill_text_base.replace("deals __3__% of your SPD", "deals __5__% of your SPD")
        skill_text_ur = skill_text_base.replace("deals __3__% of your SPD", "deals __6__% of your SPD")
        skill_text_sr = skill_text_sr.replace("deals __30__% of your opponent", "deals __54__% of your opponent")
        skill_text_ur = skill_text_ur.replace("deals __30__% of your opponent", "deals __60__% of your opponent")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Undying Will":
        skill_text_base = text_field_1.replace("<:UNDYING_WILL:1193149969318805574>", "<:Undying_Will:1335616441176555580>")
        skill_text_sr = skill_text_base.replace("with __10__% HP", "with __18__% HP")
        skill_text_ur = skill_text_base.replace("with __10__% HP", "with __20__% HP")
        skill_text_sr = skill_text_sr.replace("dealt by __20__%.", "dealt by __36__%.")
        skill_text_ur = skill_text_ur.replace("dealt by __20__%.", "dealt by __40__%.")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Unlucky Coin":
        skill_text_base = text_field_1.replace("<:UNLUCKY_COIN:844135329862254613>", "<:Unlucky_Coin:1335616425603235840>")
        skill_text_sr = skill_text_base.replace("a __20__ sided", "a __36__ sided")
        skill_text_ur = skill_text_base.replace("a __20__ sided", "a __40__ sided")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Omniscient Hack":
        skill_text_base = text_field_1.replace("<:OMNISCIENT_HACK:1135644633012121681>", "<:Omniscient_Hack:1336069861843144806>")
        skill_text_sr = skill_text_base.replace("taken by __18__%", "taken by __32__%")
        skill_text_ur = skill_text_base.replace("taken by __18__%", "taken by __36__%")
        skill_text_sr = skill_text_sr.replace("dealt by __15__%", "dealt by __27__%")
        skill_text_ur = skill_text_ur.replace("dealt by __15__%", "dealt by __30__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Miracle Injection":
        skill_text_base = text_field_1.replace("<:MIRACLE_INJECTION:833383898762182686>", "<:Miracle_Injection:1335616777895284776>")
        skill_text_sr = skill_text_base.replace("max HP by __10__%.", "max HP by __18__%.")
        skill_text_ur = skill_text_base.replace("max HP by __10__%.", "max HP by __20__%.")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Mana Reaver":
        skill_text_base = text_field_1.replace("<:MANA_REAVER:723700092451684446>", "<:Mana_Reaver:1335616788196753408>")
        skill_text_sr = skill_text_base.replace("Absorb up to __20__%", "Absorb up to __36__%")
        skill_text_ur = skill_text_base.replace("Absorb up to __20__%", "Absorb up to __40__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Lethal Clarity":
        skill_text_base = text_field_1.replace("<:LETHAL_CLARITY:1219500167716143136>", "<:Lethal_Clarity:1335616806890504313>")
        skill_text_sr = skill_text_base.replace("by __12__%.", "by __21__%.")
        skill_text_ur = skill_text_base.replace("by __12__%.", "by __24__%.")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Grievous Limiter":
        skill_text_base = text_field_1.replace("<:GRIEVOUS_LIMITER:723700679897645137>", "<:Grievous_Limiter:1335616818483691580>")
        skill_text_sr = skill_text_base.replace("enemy familiars by __40__%.", "enemy familiars by __72__%.")
        skill_text_ur = skill_text_base.replace("enemy familiars by __40__%.", "enemy familiars by __80__%.")
        skill_text_sr = skill_text_sr.replace("increases by __5__%", "increases by __9__%")
        skill_text_ur = skill_text_ur.replace("increases by __5__%", "increases by __10__%")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Underdog":
        skill_text_base = text_field_1.replace("<:UNDERDOG:708452954587529226>", "<:Underdog:1336428564739915837>")
        skill_text_sr = skill_text_base.replace("all allies by __15__%.", "all allies by __27__%.")
        skill_text_ur = skill_text_base.replace("all allies by __15__%.", "all allies by __30__%.")
        return skill_text_base, skill_text_sr, skill_text_ur
    if skill_name == "Atmospheric Acceleration":
        skill_text_base = text_field_1.replace("<:ATMOSPHERIC_ACCELERATION:1349909434054213673>", "<:ATMOSPHERIC_ACCELERATION:1356654809842974770>")
        skill_text_sr = skill_text_base.replace("all allied familiars by __15__%", "all allied familiars by __27__%")
        skill_text_ur = skill_text_base.replace("all allied familiars by __15__%.", "all allied familiars by __30__%")
        skill_text_sr = skill_text_sr.replace("their SPD increased further by __3__%,", "their SPD increased further by __5__%,")
        skill_text_ur = skill_text_ur.replace("their SPD increased further by __3__%,", "their SPD increased further by __6__%,")
        skill_text_sr = skill_text_sr.replace("opposing team take __15__% of the difference", "opposing team take __36__% of the difference")
        skill_text_ur = skill_text_ur.replace("opposing team take __15__% of the difference", "opposing team take __40__% of the difference")
        return skill_text_base, skill_text_sr, skill_text_ur
