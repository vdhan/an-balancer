import argparse
import math
from pathlib import Path

FIELDS = (
    'max',
    'min',
    'val',
    'level',
    'attack',
    'defense',
    'hitPoints',
    'damage',
    'speed',
    'upgrades',
    'advMapAmount',
    'aiValue',
    'fightValue'
)


def calc_damage_coeff(attack, defence):
    avg_skill = 4
    a = attack + avg_skill
    d = defence + avg_skill
    if a >= d:
        return round(1 + min((a - d) * 0.05, 3))
    else:
        return round(1 - min((d - a) * 0.025, 0.7))


def calc_att_damage(attack, enemy_defence_reduction):
    """
    Each value represents defence of unupgraded and upgraded creature, for example:
    - First two values are 5 and 5, 5 is defence of pikeman and 5 is of halberdier,
    - Second two values belong to archer and marksman, and so on
    """
    std_defence = [
        5, 5, 3, 3, 8, 9, 12, 12, 7, 10, 15, 16, 20, 30, 3, 3, 7, 7, 5, 5, 8, 10, 12, 12, 14, 14, 18, 27,
        3, 4, 6, 7, 10, 10, 8, 9, 12, 12, 13, 13, 16, 24, 3, 4, 4, 4, 6, 8, 10, 10, 13, 13, 12, 14, 21, 28,
        4, 6, 5, 5, 7, 7, 9, 10, 10, 10, 16, 18, 15, 17, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 13, 14, 19, 25,
        2, 3, 5, 5, 4, 4, 7, 7, 11, 11, 12, 13, 17, 19, 5, 6, 6, 8, 14, 16, 9, 10, 11, 12, 14, 14, 18, 20,
        9, 10, 8, 10, 12, 12, 2, 2, 13, 13, 0, 10, 0, 11, 0, 9, 0, 8, 18, 18, 50, 40, 20, 30, 12, 10, 2,
        1, 5, 7, 8, 3, 7, 10, 10, 0, 5, 5, 40, 36, 32, 37, 23, 33, 25, 27, 28
    ]

    result = 0
    for i in std_defence:
        result += calc_damage_coeff(attack, i * (1 - enemy_defence_reduction))

    result /= 159
    return round(result)


def calc_def_damage(defence, general_attack_reduction):
    """
    Each value represents attack of unupgraded and upgraded creature, for example:
    - First two values are 4 and 6, 4 is attack of pikeman and 6 is of halberdier,
    - Second two values belong to archer and marksman, and so on
    """
    std_attack = [
        4, 6, 6, 6, 8, 9, 10, 12, 12, 12, 15, 16, 20, 30, 5, 6, 6, 7, 9, 9, 9, 9, 9, 9, 15, 15, 18,
        27, 3, 4, 6, 7, 7, 9, 11, 12, 12, 12, 16, 16, 19, 24, 2, 4, 6, 7, 10, 10, 10, 10, 13, 13,
        16, 16, 19, 26, 5, 6, 5, 5, 7, 7, 10, 10, 13, 13, 16, 18, 17, 19, 4, 5, 6, 6, 9, 10, 9, 10,
        14, 15, 15, 16, 19, 25, 4, 5, 7, 8, 8, 8, 13, 13, 13, 13, 15, 17, 17, 19, 3, 4, 5, 6, 10,
        11, 7, 8, 11, 12, 14, 14, 16, 18, 9, 10, 10, 8, 11, 13, 2, 2, 15, 15, 0, 8, 0, 11, 0, 9, 0,
        12, 18, 21, 50, 40, 20, 30, 17, 12, 4, 1, 6, 7, 9, 8, 14, 10, 10, 0, 0, 10, 40, 36, 32,
        35, 25, 33, 25, 25, 28
    ]

    result = 0
    for i in std_attack:
        result += calc_damage_coeff(i * (1 - general_attack_reduction), defence)

    result /= 159
    return round(result)


def calc_final(att_v, def_v, prot_power, mul):
    if att_v == 0:
        return 0
    else:
        return round(math.sqrt(att_v) * pow(def_v, prot_power) * mul)


def calculate_values(attack, defence, hit_points, min_damage, max_damage,
                     general_attack_reduction, enemy_defence_reduction):
    dmg_factor = 0.5
    prot_power_fight = 0.57  # Less for Fight value
    prot_power_ai = 0.67  # More for AI value
    mul_fight = 1
    mul_ai = 0.6

    att_v = calc_att_damage(
        attack, enemy_defence_reduction) * (dmg_factor * max_damage + (1 - dmg_factor) * min_damage) * 50 + 1

    def_v = (7 / calc_def_damage(defence, general_attack_reduction) + 1) * hit_points + 1

    final_v = calc_final(att_v, def_v, prot_power_fight, mul_fight)
    final_ai = calc_final(att_v, def_v, prot_power_ai, mul_ai)
    return final_v, final_ai


# Works for fields containing integers only
def extract_value(line, field_name):
    if ',' in line:
        comma_pos = line.find(',')
        if comma_pos < line.find(field_name):
            line = line[comma_pos + 1:]
        else:
            line = line[:comma_pos]

    if '{' in line:
        line = line[line.find('{') + 1:]

    if '}' in line:
        line = line[:line.find('}')]

    if '//' in line:
        line = line[:line.find('//')]

    val = line[line.find(':') + 1:].strip()
    return int(val)


# Returns True if given line contains specified text and text isn't commented out, false otherwise
def is_not_commented_out(line, text):
    text_pos = line.find(text)
    if text_pos == -1:
        return False

    comment_pos = line.find('//')
    if comment_pos == -1:
        return True

    return text_pos < comment_pos


def get_value_from_list(file_content, seeked_string):
    braces = 0
    text_line = ''
    for line in file_content:
        braces += line.count('{')
        braces -= line.count('}')

        if is_not_commented_out(line, seeked_string):
            if line.count('"') > 2:
                continue  # eg. "attack": "something.wav"

            if braces < 3:
                text_line = line
                break

    return extract_value(text_line, seeked_string)


def get_boolean_ability_existence(file_content, seeked_string):
    for line in file_content:
        if is_not_commented_out(line, seeked_string):
            return True

    return False


def get_max_min_damage(file_content, property_name):
    minimum = maximum = -1
    found = False
    for line in file_content:
        if is_not_commented_out(line, property_name):
            found = True

        if found:
            if is_not_commented_out(line, FIELDS[0]):
                maximum = extract_value(line, FIELDS[0])

            if is_not_commented_out(line, FIELDS[1]):
                minimum = extract_value(line, FIELDS[1])

            if '}' in line:
                found = False

    return maximum, minimum


# Replaces value which must be formatted like "VALUE_NAME" : 0,
# And not like "VALUE_NAME" : 0, "VALUE_NAME" : 0
def replace_value(file_content, search_value, write_value):
    braces = 0
    for i in range(len(file_content)):
        braces += file_content[i].count('{')
        braces -= file_content[i].count('}')
        if is_not_commented_out(file_content[i], search_value):
            if braces < 3:
                comment_content = ''
                comment_pos = file_content[i].find('//')
                if comment_pos != -1:
                    comment_content = file_content[i][comment_pos:]

                has_comma = file_content[i].count(',')
                semicolon_pos = file_content[i].find(':')
                file_content[i] = f'{file_content[i][:semicolon_pos + 1]} {write_value}'
                if has_comma:
                    file_content[i] += ','

                file_content[i] += comment_content


# Replaces two values "max" and "min" within specified property
def replace_value_min_max(file_content, search_value, write_min, write_max):
    found = False
    for i in range(len(file_content)):
        if is_not_commented_out(file_content[i], search_value):
            found = True

        # todo: change to regex method
        if found:
            if is_not_commented_out(file_content[i], FIELDS[0]):
                str_old_max = get_max_min_damage(file_content, search_value)[0]
                file_content[i] = file_content[i].replace(' ', '')  # get rid of spaces
                str_max_to_replace = f'"max":{str_old_max}'
                file_content[i] = file_content[i].replace(str_max_to_replace, f'"max": {write_max}')

            if is_not_commented_out(file_content[i], FIELDS[1]):
                str_old_min = get_max_min_damage(file_content, search_value)[1]
                file_content[i] = file_content[i].replace(' ', '')  # get rid of spaces
                str_min_to_replace = f'"min":{str_old_min}'
                file_content[i] = file_content[i].replace(str_min_to_replace, f'"min": {write_min}')

            if file_content[i].count('}'):
                break


def balance_procedure(file_content, params):
    def correct_value_within_range(value, minimum, maximum):
        if value > maximum:
            return maximum
        elif value < minimum:
            return minimum
        else:
            return value

    attack_skill = params[0]
    defence_skill = params[1]
    hit_points = params[2]
    max_damage = params[3]
    min_damage = params[4]
    level = params[5]
    if level <= 0 or level > 7:
        return params

    # todo: merge with level 1
    if attack_skill < 0:
        attack_skill = 0
    if defence_skill < 0:
        defence_skill = 0
    if min_damage < 0:
        min_damage = 0
    if max_damage < 0:
        max_damage = 0
    if hit_points < 0:
        hit_points = 1

    if level == 1:
        if attack_skill > 7:
            attack_skill = 7
        if defence_skill > 7:
            defence_skill = 7
        if max_damage > 4:
            max_damage = 4
        if min_damage > max_damage:
            min_damage = max_damage - 1
        if hit_points > 11:
            hit_points = 11
    elif level == 2:
        attack_skill = correct_value_within_range(attack_skill, 4, 10)
        defence_skill = correct_value_within_range(defence_skill, 2, 7)
        max_damage = correct_value_within_range(max_damage, 3, 5)
        min_damage = correct_value_within_range(min_damage, 1, max_damage)
        hit_points = correct_value_within_range(hit_points, 9, 16)
    elif level == 3:
        attack_skill = correct_value_within_range(attack_skill, 6, 11)
        defence_skill = correct_value_within_range(defence_skill, 3, 11)
        max_damage = correct_value_within_range(max_damage, 4, 8)
        min_damage = correct_value_within_range(min_damage, 2, max_damage)
        hit_points = correct_value_within_range(hit_points, 16, 38)
    elif level == 4:
        attack_skill = correct_value_within_range(attack_skill, 6, 14)
        defence_skill = correct_value_within_range(defence_skill, 6, 13)
        max_damage = correct_value_within_range(max_damage, 5, 13)
        min_damage = correct_value_within_range(min_damage, 2, max_damage)
        hit_points = correct_value_within_range(hit_points, 18, 66)
    elif level == 5:
        attack_skill = correct_value_within_range(attack_skill, 7, 17)
        defence_skill = correct_value_within_range(defence_skill, 7, 17)
        max_damage = correct_value_within_range(max_damage, 6, 22)
        min_damage = correct_value_within_range(min_damage, 3, max_damage)
        hit_points = correct_value_within_range(hit_points, 27, 77)
    elif level == 6:
        attack_skill = correct_value_within_range(attack_skill, 11, 19)
        defence_skill = correct_value_within_range(defence_skill, 11, 19)
        max_damage = correct_value_within_range(max_damage, 9, 33)
        min_damage = correct_value_within_range(min_damage, 9, max_damage)
        hit_points = correct_value_within_range(hit_points, 63, 132)
    elif level == 7:
        attack_skill = correct_value_within_range(attack_skill, 15, 33)
        defence_skill = correct_value_within_range(defence_skill, 15, 33)
        max_damage = correct_value_within_range(max_damage, 23, 66)
        min_damage = correct_value_within_range(min_damage, 23, max_damage)
        hit_points = correct_value_within_range(hit_points, 135, 330)

    replace_value(file_content, FIELDS[4], attack_skill)
    replace_value(file_content, FIELDS[5], defence_skill)
    replace_value(file_content, FIELDS[6], hit_points)
    replace_value_min_max(file_content, FIELDS[7], min_damage, max_damage)
    return [attack_skill, defence_skill, hit_points, max_damage, min_damage]


def get_value_of_ability(file_content):
    found = False
    for line in file_content:
        if is_not_commented_out(line, 'abilities'):
            found = True

        if found:
            if is_not_commented_out(line, FIELDS[2]):
                return extract_value(line, FIELDS[2])

            if line.count('}'):
                found = False

    return -1


# Main procedure balancing files
def correct_values(file_content):
    level = get_value_from_list(file_content, FIELDS[3])
    defence_skill = get_value_from_list(file_content, FIELDS[5])
    attack_skill = get_value_from_list(file_content, FIELDS[4])
    hit_points = get_value_from_list(file_content, FIELDS[6])
    speed = get_value_from_list(file_content, FIELDS[8])

    is_two_hex = get_boolean_ability_existence(file_content, 'TWO_HEX_BREATH_ATTACK')
    is_poison = get_boolean_ability_existence(file_content, 'POISON')
    is_acid_breath = get_boolean_ability_existence(file_content, 'ACID_BREATH')
    is_double_damage = get_boolean_ability_existence(file_content, 'DOUBLE_DAMAGE_CHANCE')
    is_minimum_damage = get_boolean_ability_existence(file_content, 'ALWAYS_MINIMUM_DAMAGE')
    is_maximum_damage = get_boolean_ability_existence(file_content, 'ALWAYS_MAXIMUM_DAMAGE')
    is_additional_attack = get_boolean_ability_existence(file_content, 'ADDITIONAL_ATTACK')
    is_three_headed_attack = get_boolean_ability_existence(file_content, 'THREE_HEADED_ATTACK')
    is_attacks_all_adjacent = get_boolean_ability_existence(file_content, 'ATTACKS_ALL_ADJACENT')
    is_enemy_defence_reduction = get_boolean_ability_existence(file_content, 'ENEMY_DEFENCE_REDUCTION')
    is_general_attack_reduction = get_boolean_ability_existence(file_content, 'GENERAL_ATTACK_REDUCTION')

    min_max = get_max_min_damage(file_content, FIELDS[7])
    min_damage = min_max[1]
    max_damage = min_max[0]

    params = [attack_skill, defence_skill, hit_points, max_damage, min_damage, level]
    out_params = balance_procedure(file_content, params)
    attack_skill = out_params[0]
    defence_skill = out_params[1]
    hit_points = out_params[2]
    max_damage = out_params[3]
    min_damage = out_params[4]

    is_upgraded = not get_boolean_ability_existence(file_content, FIELDS[9])
    min_quantity = max_quantity = 0
    if level == 1:
        if is_upgraded:
            max_quantity = 30
            min_quantity = 20
        else:
            max_quantity = 50
            min_quantity = 20
    elif level == 2:
        if is_upgraded:
            max_quantity = 25
            min_quantity = 16
        else:
            max_quantity = 30
            min_quantity = 25
    elif level == 3:
        if is_upgraded:
            max_quantity = 20
            min_quantity = 12
        else:
            max_quantity = 25
            min_quantity = 12
    elif level == 4:
        if is_upgraded:
            max_quantity = 16
            min_quantity = 10
        else:
            max_quantity = 20
            min_quantity = 10
    elif level == 5:
        if is_upgraded:
            max_quantity = 12
            min_quantity = 8
        else:
            max_quantity = 16
            min_quantity = 8
    elif level == 6:
        if is_upgraded:
            max_quantity = 10
            min_quantity = 5
        else:
            max_quantity = 12
            min_quantity = 5
    elif level == 7:
        if is_upgraded:
            max_quantity = 8
            min_quantity = 3
        else:
            max_quantity = 10
            min_quantity = 4

    replace_value_min_max(file_content, FIELDS[10], min_quantity, max_quantity)

    corr_max_damage = max_damage
    corr_min_damage = min_damage
    if is_minimum_damage:
        corr_max_damage = min_damage
    if is_maximum_damage:
        corr_min_damage = max_damage
    if is_three_headed_attack:
        corr_max_damage *= 3
    if is_attacks_all_adjacent:
        corr_max_damage *= 6
    if is_additional_attack:
        corr_max_damage *= 2
    if is_two_hex:
        corr_max_damage *= 2
    if is_acid_breath:
        corr_max_damage += get_value_of_ability(file_content)
    if is_poison:
        corr_max_damage += get_value_of_ability(file_content)
    if is_double_damage:
        double_damage_chance = get_value_of_ability(file_content)
        if double_damage_chance > 0:
            corr_max_damage += max_damage

    enemy_defence_reduction = 0
    general_attack_reduction = 0
    if is_enemy_defence_reduction:
        enemy_defence_reduction = get_value_of_ability(file_content) / 100
        if enemy_defence_reduction >= 1:
            enemy_defence_reduction = 1

    if is_general_attack_reduction:
        general_attack_reduction = get_value_of_ability(file_content) / 100
        if general_attack_reduction >= 1:
            general_attack_reduction = 1

    out = calculate_values(attack_skill, defence_skill, hit_points, corr_min_damage, corr_max_damage,
                           general_attack_reduction, enemy_defence_reduction)
    fight_value = out[0]
    ai_value = out[1]

    corr_fight_value = fight_value
    corr_ai_value = ai_value

    '''
    1 - name of ability to search (percents)
    2 - bonus to fight value (percents)
    3 - bonus to ai value (percents)
    4 - bonus to damage (percents) not used now
    5 - reserved
    6 - reserved
    '''
    abilities = (
        ['NON_LIVING', 2, 2, 0, 0, 0],
        ['UNDEAD', 2, 2, 0, 0, 0],
        ['DRAGON_NATURE', 1, 1, 0, 0, 0],
        ['KING1', 1, 1, 0, 0, 0],
        ['KING2', 2, 2, 0, 0, 0],
        ['KING3', 3, 3, 0, 0, 0],
        ['FEARLESS', 5, 5, 0, 0, 0],
        ['NO_LUCK', 1, 1, 0, 0, 0],
        ['NO_MORALE', 1, 1, 0, 0, 0],
        ['SELF_MORALE', 2, 2, 0, 0, 0],
        ['SELF_LUCK', 2, 2, 0, 0, 0],
        ['FLYING', 7, 7, 0, 0, 0],
        ['SHOOTER', 10, 10, 0, 0, 0],
        ['CHARGE_IMMUNITY', 2, 2, 0, 0, 0],
        ['ADDITIONAL_ATTACK', 0, 0, 0, 0, 0],
        ['UNLIMITED_RETALIATIONS', 10, 10, 0, 0, 0],
        ['ADDITIONAL_RETALIATION', 5, 5, 0, 0, 0],
        ['JOUSTING', 3, 3, 0, 0, 0],
        ['HATE', 1, 1, 0, 0, 0],
        ['SPELL_LIKE_ATTACK', 3, 3, 0, 0, 0],
        ['THREE_HEADED_ATTACK', 0, 0, 0, 0, 0],
        ['ATTACKS_ALL_ADJACENT', 0, 0, 0, 0, 0],
        ['TWO_HEX_ATTACK_BREATH', 0, 0, 0, 0, 0],
        ['RETURN_AFTER_STRIKE', 3, 3, 0, 0, 0],
        ['ENEMY_DEFENCE_REDUCTION', 0, 0, 0, 0, 0],
        ['GENERAL_DAMAGE_REDUCTION', 5, 5, 0, 0, 0],
        ['GENERAL_ATTACK_REDUCTION', 0, 0, 0, 0, 0],
        ['DEFENSIVE_STANCE', 5, 5, 0, 0, 0],
        ['NO_DISTANCE_PENALTY', 7, 7, 0, 0, 0],
        ['NO_MELEE_PENALTY', 5, 5, 0, 0, 0],
        ['NO_WALL_PENALTY', 3, 3, 0, 0, 0],
        ['FREE_SHOOTING', 10, 10, 0, 0, 0],
        ['BLOCKS_RETALIATION', 5, 5, 0, 0, 0],
        ['CATAPULT', 10, 10, 0, 0, 0],
        ['CHANGES_SPELL_COST_FOR_ALLY', 7, 7, 0, 0, 0],
        ['CHANGES_SPELL_COST_FOR_ENEMY', 7, 7, 0, 0, 0],
        ['SPELL_RESISTANCE_AURA', 5, 5, 0, 0, 0],
        ['HP_REGENERATION', 2, 2, 0, 0, 0],
        ['FULL_HP_REGENERATION', 3, 3, 0, 0, 0],
        ['MANA_DRAIN', 3, 3, 0, 0, 0],
        ['MANA_CHANNELING', 3, 3, 0, 0, 0],
        ['LIFE_DRAIN', 5, 5, 0, 0, 0],
        ['DOUBLE_DAMAGE_CHANCE', 0, 0, 0, 0, 0],
        ['FEAR', 10, 10, 0, 0, 0],
        ['HEALER', 3, 3, 0, 0, 0],
        ['FIRE_SHIELD', 7, 7, 0, 0, 0],
        ['MAGIC_MIRROR', 4, 4, 0, 0, 0],
        ['ACID_BREATH', 3, 3, 0, 0, 0],
        ['DEATH_STARE', 10, 10, 0, 0, 0],
        ['SPELLCASTER', 5, 5, 0, 0, 0],
        ['ENCHANTER', 10, 10, 0, 0, 0],
        ['RANDOM_SPELLCASTER', 4, 4, 0, 0, 0],
        ['SPELL_AFTER_ATTACK', 3, 3, 0, 0, 0],
        ['SPELL_BEFORE_ATTACK', 3, 3, 0, 0, 0],
        ['CASTS', 0, 0, 0, 0, 0],
        ['SPECIFIC_SPELL_POWER', 0, 0, 0, 0, 0],
        ['CREATURE_SPELL_POWER', 0, 0, 0, 0, 0],
        ['CREATURE_ENCHANT_POWER', 0, 0, 0, 0, 0],
        ['DAEMON_SUMMONING', 7, 7, 0, 0, 0],
        ['REBIRTH', 5, 5, 0, 0, 0],
        ['ENCHANTED', 5, 5, 0, 0, 0],
        ['LEVEL_SPELL_IMMUNITY', 10, 10, 0, 0, 0],
        ['MAGIC_RESISTANCE', 5, 5, 0, 0, 0],
        ['SPELL_DAMAGE_REDUCTION', 2, 2, 0, 0, 0],
        ['MORE_DAMAGE_FROM_SPELL', -2, -2, 0, 0, 0],
        ['WATER_IMMUNITY', 2, 2, 0, 0, 0],
        ['EARTH_IMMUNITY', 2, 2, 0, 0, 0],
        ['AIR_IMMUNITY', 2, 2, 0, 0, 0],
        ['MIND_IMMUNITY', 2, 2, 0, 0, 0],
        ['SPELL_IMMUNITY', 1, 1, 0, 0, 0],
        ['DIRECT_DAMAGE_IMMUNITY', 10, 10, 0, 0, 0],
        ['RECEPTIVE', 3, 3, 0, 0, 0],
        ['POISON', 3, 3, 0, 0, 0],
        ['SLAYER', 3, 3, 0, 0, 0],
        ['BIND_EFFECT', 0, 0, 0, 0, 0],
        ['FORGETFULL', -7, -7, 0, 0, 0],
        ['NOT_ACTIVE', -10, -10, 0, 0, 0],
        ['ALWAYS_MINIMUM_DAMAGE', -5, -5, 0, 0, 0],
        ['ALWAYS_MAXIMUM_DAMAGE', 7, 7, 0, 0, 0],
        ['ATTACKS_NEAREST_CREATURE', -5, -5, 0, 0, 0],
        ['IN_FRENZY', 2, 2, 0, 0, 0],
        ['HYPNOTIZED', -10, -10, 0, 0, 0]
    )

    for ability in abilities:
        if get_boolean_ability_existence(file_content, ability[0]):
            corr_fight_value = corr_fight_value * ((100 + ability[1]) / 100)
            corr_ai_value = corr_ai_value * ((100 + ability[2]) / 100)

    if speed > 5:
        if speed <= 10:
            corr_fight_value *= 1.05
            corr_ai_value *= 1.05
        else:
            corr_fight_value *= 1.1
            corr_ai_value *= 1.1

    replace_value(file_content, FIELDS[11], int(corr_ai_value))
    replace_value(file_content, FIELDS[12], int(corr_fight_value))
    return file_content


def create_balanced_file(prefix, file_name):
    with file_name.open() as f:
        file_content = [text.strip('\n') for text in f.readlines()]

    file_content = correct_values(file_content)
    balanced_file = Path(f'{prefix}/{file_name}')
    with balanced_file.open('w') as f:
        for line in file_content:
            f.write(f'{line}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="An's Balancer calculates AI and Fight Values of creatures in VCMI.\n"
                    'Based on GrayFace and Macron1 formulas (http://wforum.heroes35.net/)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'paths',
        help='path to json file of creature need to calculate AI/Fight Value',
        nargs='+',
        metavar='path')
    parser.add_argument('-v', '--version', action='version', version='1.0')
    args = parser.parse_args()

    PREFIX = 'balanced'
    Path(f'{PREFIX}').mkdir(exist_ok=True)

    paths = args.paths
    for item in paths:
        path = Path(item)
        if path.is_dir():
            Path(f'{PREFIX}/{path}').mkdir(exist_ok=True)

            files = path.iterdir()
            for file in files:
                if file.is_file():
                    create_balanced_file(PREFIX, file)
        elif path.is_file():
            create_balanced_file(PREFIX, path)
        else:
            print(f'Warning: {path} is not file nor directory')

    print('Done.')
