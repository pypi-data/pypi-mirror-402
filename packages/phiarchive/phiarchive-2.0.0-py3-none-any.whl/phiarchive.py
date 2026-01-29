import concurrent.futures
import requests
import zipfile
import io
import struct
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import quote, unquote
from xml.etree import ElementTree
from xml.dom import minidom

class PhiArchive:
    CLOUD_BASE_URL = "https://rak3ffdi.cloud.tds1.tapapis.cn/1.1/"
    CLOUD_HEADERS = {
        "X-LC-Id": "rAK3FfdieFob2Nn8Am",
        "X-LC-Key": "Qr9AEqtuoSVS3zeD6iVbM4ZC0AtkJcQ89tywVyi0",
        "User-Agent": "LeanCloud-CSharp-SDK/1.0.3",
        "Accept": "application/json"
    }
    
    CLOUD_AES_KEY = base64.b64decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
    CLOUD_AES_IV = base64.b64decode("Kk/wisgNYwcAV8WVGMgyUw==")
    
    LOCAL_AES_KEY = bytes.fromhex("627ff1942185e011c815e81e639b9a00001c766b826c29bd96578589f19a6fd6")
    LOCAL_AES_IV = bytes.fromhex("be56167f83da3befeff81861a5c5f3cd")
    
    DIFF_MAP = {0: "EZ", 1: "HD", 2: "IN", 3: "AT", 4: "Legacy"}
    
    def __init__(self):
        self.session_token = None
        self.decrypted_data = {}
    
    def set_session_token(self, token):
        self.session_token = token
    
    def _cloud_headers(self):
        headers = self.CLOUD_HEADERS.copy()
        if self.session_token:
            headers["X-LC-Session"] = self.session_token
        return headers
    
    def cloud_get_user_info(self):
        try:
            endpoint = "users/me"
            response = requests.get(self.CLOUD_BASE_URL + endpoint, headers=self._cloud_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def cloud_get_save_info(self):
        try:
            endpoint = "classes/_GameSave?limit=1"
            response = requests.get(self.CLOUD_BASE_URL + endpoint, headers=self._cloud_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def cloud_get_summary_and_name(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_user = executor.submit(self.cloud_get_user_info)
            future_save = executor.submit(self.cloud_get_save_info)
            user_info = future_user.result()
            save_info = future_save.result()
        nickname = user_info.get("nickname", "Unknown")
        return {"nickname": nickname, "user_info": user_info, "summary": save_info}
    
    def cloud_get_save_url(self, summary_and_name):
        return summary_and_name["summary"]["results"][0]["gameFile"]['url']
    
    def cloud_get_all_files(self):
        summary_and_name = self.cloud_get_summary_and_name()
        save_url = self.cloud_get_save_url(summary_and_name)
        save = requests.get(save_url, headers=self._cloud_headers())
        zip_data = io.BytesIO(save.content)
        
        AllFileDecode = {}
        with zipfile.ZipFile(zip_data, 'r') as gameSaveFile:
            files = ['gameRecord', 'gameKey', 'gameProgress', 'settings', 'user']
            for file_name in files:
                with gameSaveFile.open(file_name) as file_in_zip:
                    file_data = file_in_zip.read()
                    decrypt_method = getattr(self, f'_cloud_decrypt_{file_name}')
                    AllFileDecode[file_name] = decrypt_method(file_data)
        
        AllFileDecode["summary"] = summary_and_name["summary"]
        AllFileDecode["nickname"] = summary_and_name["nickname"]
        AllFileDecode["userInfo"] = summary_and_name["user_info"]
        return AllFileDecode
    
    def _cloud_decrypt_gameRecord(self, game_record_bytes):
        def read_varint(data, pos):
            if data[pos] > 127:
                pos += 2
                return ((data[pos-2] & 0b01111111) ^ (data[pos-1] << 7)), pos
            else:
                return data[pos], pos + 1
        
        def read_string(data, pos):
            length, pos = read_varint(data, pos)
            return data[pos:pos+length].decode('utf-8'), pos + length
        
        if game_record_bytes[0] == 1:
            game_record_bytes = game_record_bytes[1:]
        
        cipher = AES.new(self.CLOUD_AES_KEY, AES.MODE_CBC, self.CLOUD_AES_IV)
        decrypted_data = unpad(cipher.decrypt(game_record_bytes), AES.block_size)
        
        result = {}
        pos = 0
        song_count, pos = read_varint(decrypted_data, pos)
        
        for _ in range(song_count):
            song_name, pos = read_string(decrypted_data, pos)
            song_id = song_name[:-2] if song_name.endswith(".0") else song_name
            data_len, pos = read_varint(decrypted_data, pos)
            end_pos = pos + data_len
            unlock_byte, fc_byte = decrypted_data[pos], decrypted_data[pos+1]
            pos += 2
            
            song_data = {}
            for diff_idx in range(5):
                if (unlock_byte >> diff_idx) & 1:
                    score = struct.unpack("<I", decrypted_data[pos:pos+4])[0]
                    acc = struct.unpack("<f", decrypted_data[pos+4:pos+8])[0]
                    pos += 8
                    diff_name = self.DIFF_MAP[diff_idx]
                    if diff_name != "Legacy":
                        song_data[diff_name] = {
                            "score": score,
                            "acc": round(acc, 4),
                            "ifFC": bool((fc_byte >> diff_idx) & 1)
                        }
            
            if song_data:
                result[song_id] = song_data
            pos = end_pos
        
        return json.dumps(result, ensure_ascii=False)
    
    def _cloud_decrypt_gameKey(self, game_key_bytes):
        def read_varint(data, pos):
            if data[pos] > 127:
                pos += 2
                return ((data[pos-2] & 0b01111111) ^ (data[pos-1] << 7)), pos
            else:
                return data[pos], pos + 1
        
        def read_string(data, pos):
            length, pos = read_varint(data, pos)
            return data[pos:pos+length].decode('utf-8'), pos + length
        
        def bits_to_list(byte_val, length=8):
            return [(byte_val >> i) & 1 for i in range(length)]
        
        if game_key_bytes[0] in [2, 3]:
            game_key_bytes = game_key_bytes[1:]
        
        cipher = AES.new(self.CLOUD_AES_KEY, AES.MODE_CBC, self.CLOUD_AES_IV)
        decrypted_data = unpad(cipher.decrypt(game_key_bytes), AES.block_size)
        
        result = {}
        pos = 0
        key_sum, pos = read_varint(decrypted_data, pos)
        
        key_list = {}
        for _ in range(key_sum):
            name, pos = read_string(decrypted_data, pos)
            length, pos = read_varint(decrypted_data, pos)
            type_byte = decrypted_data[pos]
            pos += 1
            flag = []
            for _ in range(length - 1):
                flag_byte = decrypted_data[pos]
                pos += 1
                flag.append(flag_byte)
            key_list[name] = {"type": bits_to_list(type_byte, 5), "flag": flag}
        
        result["keyList"] = key_list
        
        if len(decrypted_data) - pos >= 6:
            lanota_keys_byte = decrypted_data[pos]
            result["lanotaReadKeys"] = bits_to_list(lanota_keys_byte, 6)
            pos += 1
        
        if len(decrypted_data) - pos >= 1:
            camellia_key_byte = decrypted_data[pos]
            result["camelliaReadKey"] = bits_to_list(camellia_key_byte, 1)
            pos += 1
        
        if len(decrypted_data) - pos >= 1:
            side_story_byte = decrypted_data[pos]
            result["sideStory4BeginReadKey"] = side_story_byte
            pos += 1
        
        if len(decrypted_data) - pos >= 1:
            old_score_byte = decrypted_data[pos]
            result["oldScoreClearedV390"] = old_score_byte
            pos += 1
        
        return json.dumps(result, ensure_ascii=False)
    
    def _cloud_decrypt_gameProgress(self, game_progress_bytes):
        def read_varint(data, pos):
            if data[pos] > 127:
                pos += 2
                return ((data[pos-2] & 0b01111111) ^ (data[pos-1] << 7)), pos
            else:
                return data[pos], pos + 1
        
        def read_string(data, pos):
            length, pos = read_varint(data, pos)
            return data[pos:pos+length].decode('utf-8'), pos + length
        
        def bits_to_list(byte_val, length=8):
            return [(byte_val >> i) & 1 for i in range(length)]
        
        def money_read(data, pos):
            money = []
            for _ in range(5):
                money_val, pos = read_varint(data, pos)
                money.append(money_val)
            return money, pos
        
        file_head = game_progress_bytes[0]
        if file_head in [3, 4]:
            game_progress_bytes = game_progress_bytes[1:]
        
        cipher = AES.new(self.CLOUD_AES_KEY, AES.MODE_CBC, self.CLOUD_AES_IV)
        decrypted_data = unpad(cipher.decrypt(game_progress_bytes), AES.block_size)
        
        result = {}
        pos = 0
        
        result["isFirstRun"] = bool((decrypted_data[pos] >> 0) & 1)
        result["legacyChapterFinished"] = bool((decrypted_data[pos] >> 1) & 1)
        result["alreadyShowCollectionTip"] = bool((decrypted_data[pos] >> 2) & 1)
        result["alreadyShowAutoUnlockINTip"] = bool((decrypted_data[pos] >> 3) & 1)
        pos += 1
        
        completed, pos = read_string(decrypted_data, pos)
        result["completed"] = completed
        
        song_update_info, pos = read_varint(decrypted_data, pos)
        result["songUpdateInfo"] = song_update_info
        
        challenge_mode_rank = struct.unpack("<H", decrypted_data[pos:pos+2])[0]
        result["challengeModeRank"] = challenge_mode_rank
        pos += 2
        
        money, pos = money_read(decrypted_data, pos)
        result["money"] = money
        
        result["unlockFlagOfSpasmodic"] = bits_to_list(decrypted_data[pos], 4)
        pos += 1
        
        result["unlockFlagOfIgallta"] = bits_to_list(decrypted_data[pos], 4)
        pos += 1
        
        result["unlockFlagOfRrharil"] = bits_to_list(decrypted_data[pos], 4)
        pos += 1
        
        result["flagOfSongRecordKey"] = bits_to_list(decrypted_data[pos], 1)
        pos += 1
        
        result["randomVersionUnlocked"] = bits_to_list(decrypted_data[pos], 6)
        pos += 1
        
        result["chapter8UnlockBegin"] = bool((decrypted_data[pos] >> 0) & 1)
        result["chapter8UnlockSecondPhase"] = bool((decrypted_data[pos] >> 1) & 1)
        result["chapter8Passed"] = bool((decrypted_data[pos] >> 2) & 1)
        pos += 1
        
        result["chapter8SongUnlocked"] = bits_to_list(decrypted_data[pos], 6)
        pos += 1
        
        if file_head == 4 and pos < len(decrypted_data):
            result["flagOfSongRecordKeyTakumi"] = bits_to_list(decrypted_data[pos], 3)
            pos += 1
        
        return json.dumps(result, ensure_ascii=False)
    
    def _cloud_decrypt_settings(self, settings_bytes):
        def read_varint(data, pos):
            if data[pos] > 127:
                pos += 2
                return ((data[pos-2] & 0b01111111) ^ (data[pos-1] << 7)), pos
            else:
                return data[pos], pos + 1
        
        def read_string(data, pos):
            length, pos = read_varint(data, pos)
            return data[pos:pos+length].decode('utf-8'), pos + length
        
        def bit_read(data, index):
            return (data >> index) & 1
        
        if settings_bytes[0] == 1:
            settings_bytes = settings_bytes[1:]
        
        cipher = AES.new(self.CLOUD_AES_KEY, AES.MODE_CBC, self.CLOUD_AES_IV)
        decrypted_data = unpad(cipher.decrypt(settings_bytes), AES.block_size)
        
        result = {}
        pos = 0
        
        result["chordSupport"] = bool(bit_read(decrypted_data[pos], 0))
        result["fcAPIndicator"] = bool(bit_read(decrypted_data[pos], 1))
        result["enableHitSound"] = bool(bit_read(decrypted_data[pos], 2))
        result["lowResolutionMode"] = bool(bit_read(decrypted_data[pos], 3))
        pos += 1
        
        device_name, pos = read_string(decrypted_data, pos)
        result["deviceName"] = device_name
        
        bright = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["bright"] = round(bright, 4)
        pos += 4
        
        music_volume = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["musicVolume"] = round(music_volume, 4)
        pos += 4
        
        effect_volume = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["effectVolume"] = round(effect_volume, 4)
        pos += 4
        
        hit_sound_volume = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["hitSoundVolume"] = round(hit_sound_volume, 4)
        pos += 4
        
        sound_offset = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["soundOffset"] = round(sound_offset, 4)
        pos += 4
        
        note_scale = struct.unpack("<f", decrypted_data[pos:pos+4])[0]
        result["noteScale"] = round(note_scale, 4)
        pos += 4
        
        return json.dumps(result, ensure_ascii=False)
    
    def _cloud_decrypt_user(self, user_bytes):
        def read_varint(data, pos):
            if data[pos] > 127:
                pos += 2
                return ((data[pos-2] & 0b01111111) ^ (data[pos-1] << 7)), pos
            else:
                return data[pos], pos + 1
        
        def read_string(data, pos):
            length, pos = read_varint(data, pos)
            return data[pos:pos+length].decode('utf-8'), pos + length
        
        if user_bytes[0] == 1:
            user_bytes = user_bytes[1:]
        
        cipher = AES.new(self.CLOUD_AES_KEY, AES.MODE_CBC, self.CLOUD_AES_IV)
        decrypted_data = unpad(cipher.decrypt(user_bytes), AES.block_size)
        
        result = {}
        pos = 0
        
        result["showPlayerId"] = decrypted_data[pos]
        pos += 1
        
        self_intro, pos = read_string(decrypted_data, pos)
        result["selfIntro"] = self_intro
        
        avatar, pos = read_string(decrypted_data, pos)
        result["avatar"] = avatar
        
        background, pos = read_string(decrypted_data, pos)
        result["background"] = background
        
        return json.dumps(result, ensure_ascii=False)
    
    @staticmethod
    def local_decrypt_string(data):
        decoded = unquote(data)
        try:
            encrypted_data = base64.b64decode(decoded)
            cipher = AES.new(PhiArchive.LOCAL_AES_KEY, AES.MODE_CBC, PhiArchive.LOCAL_AES_IV)
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted.decode('utf-8'), True
        except Exception:
            return decoded, False
    
    @staticmethod
    def local_encrypt_string(data):
        if data is None:
            data = ''
        encode_data = data.encode('utf-8')
        pad_data = pad(encode_data, AES.block_size)
        encrypt_data = AES.new(PhiArchive.LOCAL_AES_KEY, AES.MODE_CBC, PhiArchive.LOCAL_AES_IV).encrypt(pad_data)
        encoded_data = base64.b64encode(encrypt_data)
        return quote(encoded_data).replace('/', '%2F')
    
    def local_decrypt_xml(self, xml_path, output_path):
        skip_keys = []
        saveTree = ElementTree.parse(xml_path)
        saveData = saveTree.getroot()
        
        for data in saveData.iter():
            if data.tag == 'map':
                continue
            elif data.tag == 'string':
                data.attrib['name'], skip = self.local_decrypt_string(data.attrib.get('name', ''))
                if skip and data.text is not None:
                    data.text, _ = self.local_decrypt_string(data.text)
                elif data.text is not None:
                    data.text = unquote(data.text)
                    skip_keys.append(data.attrib.get('name', ''))
            elif data.tag == 'int':
                data.attrib['name'] = unquote(data.attrib.get('name', ''))
        
        saveTree.write(output_path, encoding='utf-8', xml_declaration=True, method='xml')
        return skip_keys
    
    def local_encrypt_xml(self, xml_path, output_path, skip_keys):
        saveTree = ElementTree.parse(xml_path)
        saveData = saveTree.getroot()
        
        for data in saveData.iter():
            if data.tag == 'map':
                continue
            elif data.tag == 'string':
                if data.attrib.get('name', '') not in skip_keys:
                    data.attrib['name'] = self.local_encrypt_string(data.attrib.get('name', ''))
                    if data.text is not None:
                        data.text = self.local_encrypt_string(data.text)
                    else:
                        data.text = ''
                else:
                    data.attrib['name'] = quote(data.attrib.get('name', '')).replace('/', '%2F')
            elif data.tag == 'int':
                data.attrib['name'] = quote(data.attrib.get('name', '')).replace('/', '%2F')
        
        saveTree.write(output_path, xml_declaration=True, method='xml', encoding='utf-8')
    
    def local_parse_to_cloud_format(self, xml_path):
        saveTree = ElementTree.parse(xml_path)
        saveData = saveTree.getroot()
        
        game_record = {}
        game_key = {"keyList": {}}
        game_progress = {}
        settings = {}
        user = {}
        
        for data in saveData.iter():
            if data.tag != 'string' or data.text is None:
                continue
            
            key = data.attrib.get('name', '')
            value = data.text
            
            if key.startswith('0key'):
                song_id = key[4:]
                if value == '1':
                    game_key["keyList"][song_id] = {"type": [0, 0, 0, 0, 0], "flag": []}
            
            elif '{' in value and '}' in value:
                try:
                    record_data = json.loads(value)
                    song_id = key
                    if song_id.endswith('.0'):
                        song_id = song_id[:-2]
                    
                    song_data = {}
                    for diff in ['EZ', 'HD', 'IN', 'AT']:
                        if diff in record_data:
                            song_data[diff] = {
                                "score": int(record_data[diff].get('s', 0)),
                                "acc": float(record_data[diff].get('a', 0)),
                                "ifFC": bool(record_data[diff].get('c', 0))
                            }
                    
                    if song_data:
                        game_record[song_id] = song_data
                except:
                    pass
            
            elif key == 'selfIntro':
                user["selfIntro"] = value
            
            elif key == 'UserIconKeyName':
                user["avatar"] = value
            
            elif key == 'UserIllustrationKeyName':
                user["background"] = value
            
            elif key == 'chordSupport':
                settings["chordSupport"] = value == '1'
            
            elif key == 'aPfCisOn':
                settings["fcAPIndicator"] = value == '1'
            
            elif key == 'hitFxIsOn':
                settings["enableHitSound"] = value == '1'
            
            elif key == 'HitFXVolume':
                try:
                    settings["hitSoundVolume"] = float(value)
                except:
                    settings["hitSoundVolume"] = 0.0
            
            elif key == 'musicVolume':
                try:
                    settings["musicVolume"] = float(value)
                except:
                    settings["musicVolume"] = 0.0
            
            elif key == 'bright':
                try:
                    settings["bright"] = float(value)
                except:
                    settings["bright"] = 0.0
            
            elif key == 'noteScale':
                try:
                    settings["noteScale"] = float(value)
                except:
                    settings["noteScale"] = 0.0
            
            elif key == 'offset':
                try:
                    settings["soundOffset"] = float(value)
                except:
                    settings["soundOffset"] = 0.0
            
            elif key == 'IsFirstRun':
                game_progress["isFirstRun"] = value == '1'
            
            elif key.startswith('NumOfMoney'):
                if 'money' not in game_progress:
                    game_progress['money'] = [0, 0, 0, 0, 0]
                idx = int(key[-1]) if key[-1].isdigit() else 0
                try:
                    game_progress['money'][idx] = int(value)
                except:
                    game_progress['money'][idx] = 0
        
        result = {
            "gameRecord": json.dumps(game_record, ensure_ascii=False),
            "gameKey": json.dumps(game_key, ensure_ascii=False),
            "gameProgress": json.dumps(game_progress, ensure_ascii=False),
            "settings": json.dumps(settings, ensure_ascii=False),
            "user": json.dumps(user, ensure_ascii=False),
            "nickname": "Local Player",
            "summary": {},
            "userInfo": {}
        }
        
        return result
    
    def cloud_parse_to_local_format(self, cloud_data, output_path):
        root = ElementTree.Element('map')
        
        game_record = json.loads(cloud_data.get("gameRecord", "{}"))
        game_key = json.loads(cloud_data.get("gameKey", "{}"))
        game_progress = json.loads(cloud_data.get("gameProgress", "{}"))
        settings = json.loads(cloud_data.get("settings", "{}"))
        user = json.loads(cloud_data.get("user", "{}"))
        
        for song_id, song_data in game_record.items():
            record_dict = {}
            for diff in ['EZ', 'HD', 'IN', 'AT']:
                if diff in song_data:
                    diff_data = song_data[diff]
                    record_dict[diff] = {
                        's': diff_data.get('score', 0),
                        'a': diff_data.get('acc', 0),
                        'c': 1 if diff_data.get('ifFC', False) else 0
                    }
            
            if record_dict:
                song_key = song_id if not song_id.endswith('.0') else song_id + '.0'
                string_elem = ElementTree.SubElement(root, 'string', {'name': song_key})
                string_elem.text = json.dumps(record_dict)
        
        for key_name, key_data in game_key.get("keyList", {}).items():
            string_elem = ElementTree.SubElement(root, 'string', {'name': f'0key{key_name}'})
            string_elem.text = '1'
        
        if 'selfIntro' in user:
            ElementTree.SubElement(root, 'string', {'name': 'selfIntro'}).text = user['selfIntro']
        
        if 'avatar' in user:
            ElementTree.SubElement(root, 'string', {'name': 'UserIconKeyName'}).text = user['avatar']
        
        if 'background' in user:
            ElementTree.SubElement(root, 'string', {'name': 'UserIllustrationKeyName'}).text = user['background']
        
        bool_settings = {
            'chordSupport': 'chordSupport',
            'fcAPIndicator': 'aPfCisOn',
            'enableHitSound': 'hitFxIsOn'
        }
        
        for cloud_key, local_key in bool_settings.items():
            if cloud_key in settings:
                ElementTree.SubElement(root, 'string', {'name': local_key}).text = '1' if settings[cloud_key] else '0'
        
        float_settings = {
            'hitSoundVolume': 'HitFXVolume',
            'musicVolume': 'musicVolume',
            'bright': 'bright',
            'noteScale': 'noteScale',
            'soundOffset': 'offset'
        }
        
        for cloud_key, local_key in float_settings.items():
            if cloud_key in settings:
                ElementTree.SubElement(root, 'string', {'name': local_key}).text = str(settings[cloud_key])
        
        if 'isFirstRun' in game_progress:
            ElementTree.SubElement(root, 'string', {'name': 'IsFirstRun'}).text = '1' if game_progress['isFirstRun'] else '0'
        
        if 'money' in game_progress:
            for i, money_val in enumerate(game_progress['money']):
                ElementTree.SubElement(root, 'string', {'name': f'NumOfMoney{i}'}).text = str(money_val)
        
        ElementTree.SubElement(root, 'string', {'name': 'PlayerIdAppear'}).text = '1'
        ElementTree.SubElement(root, 'string', {'name': 'unity.player_session_count'}).text = '1'
        ElementTree.SubElement(root, 'string', {'name': 'unity.player_sessionid'}).text = 'local_session'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            data = minidom.parseString(ElementTree.tostring(root, encoding='utf-8')).toprettyxml(indent='    ')
            f.write(data)
        
        return output_path
    
    def local_to_cloud(self, local_xml_path):
        decrypted_path = "temp_decrypted.xml"
        skip_keys = self.local_decrypt_xml(local_xml_path, decrypted_path)
        cloud_format = self.local_parse_to_cloud_format(decrypted_path)
        return cloud_format
    
    def cloud_to_local(self, cloud_data, output_path):
        local_xml = self.cloud_parse_to_local_format(cloud_data, "temp_local.xml")
        skip_keys = ["unity.player_session_count", "unity.player_sessionid"]
        self.local_encrypt_xml("temp_local.xml", output_path, skip_keys)
        return output_path
"""
PhiArchive 类使用说明
==============

基础用法:
1. 创建实例: phi = PhiArchive()
2. 设置云存档token: phi.set_session_token("your_token")
3. 调用相应方法

======================================================================
云存档功能 (需要session token)
======================================================================

1. 获取用户信息:
   user_info = phi.cloud_get_user_info()
   返回: 包含nickname, username, email等的字典

2. 获取存档摘要:
   save_info = phi.cloud_get_save_info()
   返回: 包含存档元数据的字典

3. 获取用户信息和存档摘要(并发):
   summary = phi.cloud_get_summary_and_name()
   返回: 包含nickname, user_info, summary的字典

4. 获取存档文件URL:
   url = phi.cloud_get_save_url(summary_and_name)
   参数: summary_and_name - cloud_get_summary_and_name()返回的字典
   返回: 存档文件下载URL

5. 下载并解密所有存档文件:
   all_data = phi.cloud_get_all_files()
   返回: 包含以下键的字典:
     - gameRecord: 歌曲成绩数据(JSON字符串)
     - gameKey: 解锁数据(JSON字符串)
     - gameProgress: 游戏进度数据(JSON字符串)
     - settings: 设置数据(JSON字符串)
     - user: 用户数据(JSON字符串)
     - nickname: 昵称
     - summary: 存档摘要
     - userInfo: 用户信息

======================================================================
本地存档加解密功能
======================================================================

1. 解密单个字符串:
   decrypted, success = PhiArchive.local_decrypt_string("加密字符串")
   返回: (解密后的字符串, 是否成功解密)

2. 加密单个字符串:
   encrypted = PhiArchive.local_encrypt_string("原始字符串")
   返回: 加密后的字符串

3. 解密XML存档文件:
   skip_keys = phi.local_decrypt_xml("加密存档.xml", "解密后存档.xml")
   参数:
     - 输入文件路径
     - 输出文件路径
   返回: 需要跳过加密的键列表

4. 加密XML存档文件:
   phi.local_encrypt_xml("解密存档.xml", "加密后存档.xml", skip_keys)
   参数:
     - 输入文件路径
     - 输出文件路径
     - 跳过加密的键列表(通常来自local_decrypt_xml的返回值)

======================================================================
存档格式转换功能
======================================================================

1. 本地存档转云存档格式:
   cloud_data = phi.local_to_cloud("本地存档.xml")
   返回: 云存档格式数据字典
   包含: gameRecord, gameKey, gameProgress, settings, user等

2. 云存档转本地存档格式:
   local_path = phi.cloud_to_local(cloud_data, "输出路径.xml")
   参数:
     - cloud_data: 云存档数据(cloud_get_all_files()返回的字典)
     - 输出文件路径
   返回: 生成的本地存档文件路径

3. 解析本地存档为云存档格式(不加密):
   cloud_format = phi.local_parse_to_cloud_format("解密后的本地存档.xml")
   返回: 云存档格式数据字典

4. 解析云存档为本地存档格式(不加密):
   xml_content = phi.cloud_parse_to_local_format(cloud_data, "输出路径.xml")
   参数:
     - cloud_data: 云存档数据
     - 输出文件路径
   返回: 生成的XML文件路径

======================================================================
内部解密方法 (一般不需要直接调用)
======================================================================

1. 解密游戏记录: _cloud_decrypt_gameRecord(data_bytes)
2. 解密解锁数据: _cloud_decrypt_gameKey(data_bytes)
3. 解密游戏进度: _cloud_decrypt_gameProgress(data_bytes)
4. 解密设置: _cloud_decrypt_settings(data_bytes)
5. 解密用户数据: _cloud_decrypt_user(data_bytes)

======================================================================
常用工作流示例
======================================================================

# 示例1: 从手机备份存档转换为云存档格式
1. 从手机获取存档文件: com.PigeonGames.Phigros.v2.playerprefs.xml
2. 解密存档: skip_keys = phi.local_decrypt_xml("playerprefs.xml", "decrypted.xml")
3. 转换为云存档格式: cloud_data = phi.local_to_cloud("playerprefs.xml")
4. 保存: import json; json.dump(cloud_data, file)

# 示例2: 从云存档恢复为本地存档
1. 获取云存档: cloud_data = phi.cloud_get_all_files()
2. 转换为本地格式: local_path = phi.cloud_to_local(cloud_data, "restored.xml")
3. 将restored.xml复制到手机相应目录

# 示例3: 修改本地存档后重新加密
1. 解密存档: skip_keys = phi.local_decrypt_xml("original.xml", "decrypted.xml")
2. 修改decrypted.xml文件内容
3. 重新加密: phi.local_encrypt_xml("decrypted.xml", "modified.xml", skip_keys)

======================================================================
注意事项
======================================================================

1. 云存档功能需要有效的session token
2. 本地存档加解密使用不同的AES密钥(与云存档不同)
3. local_encrypt_xml需要skip_keys参数，来自local_decrypt_xml的返回值
4. 转换过程中部分数据可能丢失，建议备份原始文件
5. 存档文件路径需要正确设置读写权限

======================================================================
快速使用示例
======================================================================

# 简化的使用流程
phi = PhiArchive()

# 模式1: 获取云存档
phi.set_session_token("your_token")
cloud_data = phi.cloud_get_all_files()

# 模式2: 解密本地存档
skip_keys = phi.local_decrypt_xml("encrypted.xml", "decrypted.xml")

# 模式3: 格式转换
cloud_data = phi.local_to_cloud("local_save.xml")
local_path = phi.cloud_to_local(cloud_data, "output.xml")

======================================================================
错误处理
======================================================================

所有方法可能抛出异常，建议使用try-except:
try:
    data = phi.cloud_get_all_files()
except Exception as e:
    print(f"错误: {e}")

======================================================================
数据格式说明
======================================================================

1. gameRecord格式:
   {
     "song_id": {
       "EZ": {"score": 1000000, "acc": 100.0, "ifFC": true},
       "HD": {"score": 1000000, "acc": 100.0, "ifFC": true},
       ...
     }
   }

2. local_parse_to_cloud_format返回格式:
   {
     "gameRecord": "JSON字符串",
     "gameKey": "JSON字符串",
     ...
   }

======================================================================
保存和加载
======================================================================

# 保存云存档数据
import json
with open('cloud_backup.json', 'w', encoding='utf-8') as f:
    json.dump(cloud_data, f, ensure_ascii=False, indent=2)

# 加载云存档数据
with open('cloud_backup.json', 'r', encoding='utf-8') as f:
    cloud_data = json.load(f)
"""