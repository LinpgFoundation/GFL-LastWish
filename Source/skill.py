# cython: language_level=3
from .battleUI import *

def skill(characterName,click_potcion,the_skill_cover_area,sangvisFerris_data,characters_data,action="detect",skill_target=None,damage_do_to_character=None):
    if action == "detect":
        skill_target = None
        if characters_data[characterName].type == "gsh-18":
            for character in characters_data:
                if characters_data[character].on_pos(click_potcion):
                    skill_target = character
                    break
        elif characters_data[characterName].type == "asval" or characters_data[characterName].type == "pp1901" or characters_data[characterName].type == "sv-98":
            for enemies in sangvisFerris_data:
                if sangvisFerris_data[enemies].on_pos(click_potcion) and sangvisFerris_data[enemies].current_hp>0:
                    skill_target = enemies
                    break
        return skill_target
    elif action == "react":
        if characters_data[characterName].type == "gsh-18":
            healed_hp = round((characters_data[skill_target].max_hp - characters_data[skill_target].current_hp)*0.3)
            characters_data[skill_target].heal(healed_hp)
            if characters_data[skill_target].dying != False:
                characters_data[skill_target].dying = False
            damage_do_to_character[skill_target] = linpg.fontRender("+"+str(healed_hp),"green",25)
        elif characters_data[characterName].type == "asval" or characters_data[characterName].type == "pp1901" or characters_data[characterName].type == "sv-98":
            the_damage = linpg.randomInt(characters_data[characterName].min_damage,characters_data[characterName].max_damage)
            sangvisFerris_data[skill_target].decreaseHp(the_damage)
            damage_do_to_character[skill_target] = linpg.fontRender("-"+str(the_damage),"red",25)
        return damage_do_to_character
