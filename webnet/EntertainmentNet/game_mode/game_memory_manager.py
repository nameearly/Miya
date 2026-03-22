"""
娓告垙妯″紡璁板繂绠＄悊鍣?
绠＄悊娓告垙妯″紡鐨勭嫭绔嬭蹇嗗垎鍖?

鏋舵瀯淇: 绉婚櫎Token绠＄悊鑱岃矗,濮旀墭缁欑嫭绔嬬殑TokenManager
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import uuid
import shutil
from core.constants import Encoding


logger = logging.getLogger(__name__)


@dataclass
class CharacterCard:
    """瑙掕壊鍗℃暟鎹?""
    character_id: str
    character_name: str
    player_id: int
    player_name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    backstory: str = ""
    notes: str = ""
    is_public: bool = True  # 鏄惁瀵瑰叾浠栫帺瀹跺彲瑙?
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.character_id:
            self.character_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CharacterCard':
        return cls(**data)


@dataclass
class GameMetadata:
    """娓告垙鍏冩暟鎹?""
    game_id: str
    game_name: str
    rule_system: str  # coc7, dnd5e, tavern
    mode_type: str    # trpg, tavern
    group_id: Optional[int] = None
    user_id: Optional[int] = None  # 绉佽亰鏃剁殑鐢ㄦ埛ID
    created_at: str = ""
    updated_at: str = ""
    auto_save_enabled: bool = True

    def __post_init__(self):
        if not self.game_id:
            self.game_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameMetadata':
        return cls(**data)


@dataclass
class SaveData:
    """瀛樻。鏁版嵁"""
    save_id: str
    game_id: str
    save_name: str
    story_progress: Dict[str, Any] = field(default_factory=dict)
    game_state: Dict[str, Any] = field(default_factory=dict)
    characters: List[Dict] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.save_id:
            self.save_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'SaveData':
        # 璁剧疆榛樿鍊?
        return cls(
            save_id=data.get('save_id', str(uuid.uuid4())),
            game_id=data.get('game_id', ''),
            save_name=data.get('save_name', '鏈懡鍚嶅瓨妗?),
            story_progress=data.get('story_progress', {}),
            game_state=data.get('game_state', {}),
            characters=data.get('characters', []),
            permissions=data.get('permissions', {}),
            created_at=data.get('created_at', '')
        )


class GameMemoryManager:
    """
    娓告垙璁板繂绠＄悊鍣?

    鑱岃矗:
    1. 绠＄悊娓告垙妯″紡鐨勭嫭绔嬭蹇嗗垎鍖?
    2. 鏀寔澶氱矑搴﹀瓨鍌?缇?鐢ㄦ埛/娓告垙瀹炰緥)
    3. 鎻愪緵鑷姩淇濆瓨鍜屾墜鍔ㄤ繚瀛樻帴鍙?
    4. 鏉冮檺楠岃瘉
    5. Token鎰熺煡鐨勬櫤鑳藉璇濆帇缂?
    """

    def __init__(self, base_path: str = "data/game_memory", token_manager=None):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 鍒涘缓瀛愮洰褰?
        (self.base_path / "groups").mkdir(exist_ok=True)
        (self.base_path / "users").mkdir(exist_ok=True)
        (self.base_path / "archives").mkdir(exist_ok=True)

        # 鍐呭瓨缂撳瓨
        self._metadata_cache: Dict[str, GameMetadata] = {}
        self._characters_cache: Dict[str, List[CharacterCard]] = {}
        self._save_data_cache: Dict[str, SaveData] = {}

        # 鏋舵瀯淇: 濮旀墭Token绠＄悊缁欑嫭绔嬬殑TokenManager
        self.token_manager = token_manager

        logger.info(f"[GameMemoryManager] 鍒濆鍖栧畬鎴? 鍩虹璺緞: {self.base_path}")

    # ==================== 娓告垙鍏冩暟鎹鐞?====================

    def create_game(
        self,
        game_name: str,
        rule_system: str,
        mode_type: str,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        auto_save_enabled: bool = True
    ) -> str:
        """
        鍒涘缓鏂版父鎴?

        Args:
            game_name: 娓告垙鍚嶇О
            rule_system: 瑙勫垯绯荤粺(coc7, dnd5e, tavern)
            mode_type: 妯″紡绫诲瀷(trpg, tavern)
            group_id: 缇ゅ彿(缇よ亰)
            user_id: 鐢ㄦ埛鍙?绉佽亰)
            auto_save_enabled: 鏄惁鍚敤鑷姩淇濆瓨

        Returns:
            game_id
        """
        game_id = str(uuid.uuid4())

        metadata = GameMetadata(
            game_id=game_id,
            game_name=game_name,
            rule_system=rule_system,
            mode_type=mode_type,
            group_id=group_id,
            user_id=user_id,
            auto_save_enabled=auto_save_enabled
        )

        # 纭畾瀛樺偍璺緞
        if group_id:
            game_dir = self.base_path / "groups" / str(group_id) / "games" / game_id
        elif user_id:
            game_dir = self.base_path / "users" / str(user_id) / "games" / game_id
        else:
            raise ValueError("蹇呴』鎻愪緵 group_id 鎴?user_id")

        game_dir.mkdir(parents=True, exist_ok=True)

        # 淇濆瓨鍏冩暟鎹?
        self._save_metadata(metadata, game_dir)

        # 鍒濆鍖栫┖鏁版嵁鏂囦欢
        (game_dir / "characters.json").write_text("[]", encoding=Encoding.UTF8)
        (game_dir / "story.json").write_text("{}", encoding=Encoding.UTF8)
        (game_dir / "save_data.json").write_text("{}", encoding=Encoding.UTF8)

        # 缂撳瓨
        self._metadata_cache[game_id] = metadata
        self._characters_cache[game_id] = []
        self._save_data_cache[game_id] = SaveData(
            save_id="autosave",
            game_id=game_id,
            save_name="鑷姩瀛樻。"
        )

        logger.info(f"[GameMemoryManager] 鍒涘缓娓告垙: {game_name} ({game_id})")
        return game_id

    def get_game_metadata(self, game_id: str) -> Optional[GameMetadata]:
        """鑾峰彇娓告垙鍏冩暟鎹?""
        # 鍏堟煡缂撳瓨
        if game_id in self._metadata_cache:
            return self._metadata_cache[game_id]

        # 浠庢枃浠跺姞杞?
        metadata_path = self._find_game_path(game_id) / "meta.json"
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding=Encoding.UTF8))
                metadata = GameMetadata.from_dict(data)
                self._metadata_cache[game_id] = metadata
                return metadata
            except Exception as e:
                logger.error(f"[GameMemoryManager] 鍔犺浇鍏冩暟鎹け璐? {e}")

        return None

    def update_game_metadata(self, game_id: str, **kwargs) -> bool:
        """鏇存柊娓告垙鍏冩暟鎹?""
        metadata = self.get_game_metadata(game_id)
        if not metadata:
            return False

        # 鏇存柊瀛楁
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        metadata.updated_at = datetime.now().isoformat()

        # 淇濆瓨鍒版枃浠?
        game_dir = self._find_game_path(game_id)
        self._save_metadata(metadata, game_dir)

        # 鏇存柊缂撳瓨
        self._metadata_cache[game_id] = metadata

        return True

    def list_games(
        self,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        mode_type: Optional[str] = None
    ) -> List[GameMetadata]:
        """
        鍒楀嚭娓告垙

        Args:
            group_id: 绛涢€夌兢鍙?
            user_id: 绛涢€夌敤鎴峰彿
            mode_type: 绛涢€夋ā寮忕被鍨?

        Returns:
            娓告垙鍏冩暟鎹垪琛?
        """
        games = []

        # 鎵弿缇ゆ父鎴?
        if group_id or user_id is None:
            groups_dir = self.base_path / "groups"
            if groups_dir.exists():
                for group_path in groups_dir.iterdir():
                    if group_id and group_path.name != str(group_id):
                        continue

                    games_dir = group_path / "games"
                    if games_dir.exists():
                        for game_dir in games_dir.iterdir():
                            metadata = self.get_game_metadata(game_dir.name)
                            if metadata and (mode_type is None or metadata.mode_type == mode_type):
                                games.append(metadata)

        # 鎵弿鐢ㄦ埛娓告垙
        if user_id or group_id is None:
            users_dir = self.base_path / "users"
            if users_dir.exists():
                for user_path in users_dir.iterdir():
                    if user_id and user_path.name != str(user_id):
                        continue

                    games_dir = user_path / "games"
                    if games_dir.exists():
                        for game_dir in games_dir.iterdir():
                            metadata = self.get_game_metadata(game_dir.name)
                            if metadata and (mode_type is None or metadata.mode_type == mode_type):
                                games.append(metadata)

        # 鎸夊垱寤烘椂闂存帓搴?
        games.sort(key=lambda x: x.created_at, reverse=True)
        return games

    def delete_game(self, game_id: str) -> bool:
        """鍒犻櫎娓告垙"""
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return False

        try:
            shutil.rmtree(game_dir)

            # 娓呴櫎缂撳瓨
            if game_id in self._metadata_cache:
                del self._metadata_cache[game_id]
            if game_id in self._characters_cache:
                del self._characters_cache[game_id]
            if game_id in self._save_data_cache:
                del self._save_data_cache[game_id]

            logger.info(f"[GameMemoryManager] 鍒犻櫎娓告垙: {game_id}")
            return True
        except Exception as e:
            logger.error(f"[GameMemoryManager] 鍒犻櫎娓告垙澶辫触: {e}")
            return False

    # ==================== 瑙掕壊鍗＄鐞?====================

    def add_character(self, game_id: str, character: CharacterCard) -> bool:
        """娣诲姞瑙掕壊鍗?""
        characters = self.get_characters(game_id)
        if characters is None:
            return False

        characters.append(character)
        self._save_characters(game_id, characters)

        # 鏇存柊缂撳瓨
        self._characters_cache[game_id] = characters

        logger.info(f"[GameMemoryManager] 娣诲姞瑙掕壊: {character.character_name}")
        return True

    def get_characters(self, game_id: str) -> Optional[List[CharacterCard]]:
        """鑾峰彇娓告垙鐨勮鑹插崱鍒楄〃"""
        # 鍏堟煡缂撳瓨
        if game_id in self._characters_cache:
            return self._characters_cache[game_id]

        # 浠庢枃浠跺姞杞?
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return None

        characters_file = game_dir / "characters.json"
        if characters_file.exists():
            try:
                data = json.loads(characters_file.read_text(encoding=Encoding.UTF8))
                characters = [CharacterCard.from_dict(d) for d in data]
                self._characters_cache[game_id] = characters
                return characters
            except Exception as e:
                logger.error(f"[GameMemoryManager] 鍔犺浇瑙掕壊鍗″け璐? {e}")

        return []

    def get_character(self, game_id: str, character_id: str) -> Optional[CharacterCard]:
        """鑾峰彇鍗曚釜瑙掕壊鍗?""
        characters = self.get_characters(game_id)
        if not characters:
            return None

        for char in characters:
            if char.character_id == character_id:
                return char

        return None

    def update_character(self, game_id: str, character_id: str, **kwargs) -> bool:
        """鏇存柊瑙掕壊鍗?""
        characters = self.get_characters(game_id)
        if not characters:
            return False

        for char in characters:
            if char.character_id == character_id:
                # 鏇存柊瀛楁
                for key, value in kwargs.items():
                    if hasattr(char, key):
                        setattr(char, key, value)

                char.updated_at = datetime.now().isoformat()
                self._save_characters(game_id, characters)
                return True

        return False

    def delete_character(self, game_id: str, character_id: str) -> bool:
        """鍒犻櫎瑙掕壊鍗?""
        characters = self.get_characters(game_id)
        if not characters:
            return False

        for i, char in enumerate(characters):
            if char.character_id == character_id:
                characters.pop(i)
                self._save_characters(game_id, characters)
                return True

        return False

    def get_visible_characters(
        self,
        game_id: str,
        player_id: int,
        is_admin: bool = False
    ) -> List[CharacterCard]:
        """
        鑾峰彇鍙鐨勮鑹插崱

        Args:
            game_id: 娓告垙ID
            player_id: 璇锋眰鐨勭帺瀹禝D
            is_admin: 鏄惁鏄鐞嗗憳

        Returns:
            鍙鐨勮鑹插崱鍒楄〃
        """
        characters = self.get_characters(game_id)
        if not characters:
            return []

        if is_admin:
            # 绠＄悊鍛樺彲浠ョ湅鍒版墍鏈夎鑹?
            return characters

        # 鏅€氱帺瀹跺彧鑳界湅鍒拌嚜宸辩殑瑙掕壊鍜屽叕寮€鐨勮鑹?
        visible = [
            char for char in characters
            if char.is_public or char.player_id == player_id
        ]

        return visible

    # ==================== 鏁呬簨杩涘害绠＄悊 ====================

    def update_story_progress(self, game_id: str, progress_data: Dict[str, Any]) -> bool:
        """鏇存柊鏁呬簨杩涘害"""
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return False

        story_file = game_dir / "story.json"

        try:
            # 鍚堝苟鐜版湁鏁版嵁
            if story_file.exists():
                existing = json.loads(story_file.read_text(encoding=Encoding.UTF8))
                existing.update(progress_data)
                progress_data = existing

            story_file.write_text(json.dumps(progress_data, ensure_ascii=False, indent=2), encoding=Encoding.UTF8)
            logger.debug(f"[GameMemoryManager] 鏇存柊鏁呬簨杩涘害: {game_id}")
            return True
        except Exception as e:
            logger.error(f"[GameMemoryManager] 鏇存柊鏁呬簨杩涘害澶辫触: {e}")
            return False

    def get_story_progress(self, game_id: str) -> Dict[str, Any]:
        """鑾峰彇鏁呬簨杩涘害"""
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return {}

        story_file = game_dir / "story.json"
        if story_file.exists():
            try:
                return json.loads(story_file.read_text(encoding=Encoding.UTF8))
            except Exception as e:
                logger.error(f"[GameMemoryManager] 鍔犺浇鏁呬簨杩涘害澶辫触: {e}")

        return {}

    # ==================== 瀛樻。绠＄悊 ====================

    def save_game(self, game_id: str, save_name: str = None) -> Optional[str]:
        """
        淇濆瓨娓告垙

        Args:
            game_id: 娓告垙ID
            save_name: 瀛樻。鍚嶇О(鍙€?

        Returns:
            save_id
        """
        metadata = self.get_game_metadata(game_id)
        if not metadata:
            return None

        # 鏀堕泦鏁版嵁
        characters = self.get_characters(game_id) or []
        story = self.get_story_progress(game_id)

        save_data = SaveData(
            save_id=str(uuid.uuid4()),
            game_id=game_id,
            save_name=save_name or f"瀛樻。_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            story_progress=story,
            game_state={"mode_type": metadata.mode_type, "rule_system": metadata.rule_system},
            characters=[char.to_dict() for char in characters],
            permissions={"auto_save": metadata.auto_save_enabled}
        )

        # 淇濆瓨鍒版枃浠?
        game_dir = self._find_game_path(game_id)
        save_file = game_dir / "save_data.json"

        try:
            save_file.write_text(json.dumps(save_data.to_dict(), ensure_ascii=False, indent=2), encoding=Encoding.UTF8)
            self._save_data_cache[game_id] = save_data

            logger.info(f"[GameMemoryManager] 淇濆瓨娓告垙: {save_name} ({save_data.save_id})")
            return save_data.save_id
        except Exception as e:
            logger.error(f"[GameMemoryManager] 淇濆瓨娓告垙澶辫触: {e}")
            return None

    def load_game(self, game_id: str) -> Optional[SaveData]:
        """鍔犺浇娓告垙瀛樻。"""
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return None

        save_file = game_dir / "save_data.json"
        if save_file.exists():
            try:
                data = json.loads(save_file.read_text(encoding=Encoding.UTF8))
                save_data = SaveData.from_dict(data)
                return save_data
            except Exception as e:
                logger.error(f"[GameMemoryManager] 鍔犺浇瀛樻。澶辫触: {e}")

        return None

    # ==================== 瀵煎嚭/瀵煎叆 ====================

    def export_archive(self, game_id: str, archive_name: str = None) -> Optional[str]:
        """
        瀵煎嚭娓告垙瀛樻。

        Args:
            game_id: 娓告垙ID
            archive_name: 瀛樻。鍚嶇О

        Returns:
            瀵煎嚭鏂囦欢璺緞
        """
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return None

        metadata = self.get_game_metadata(game_id)
        if not metadata:
            return None

        archive_name = archive_name or f"{metadata.game_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_path = self.base_path / "archives" / f"{archive_name}.json"

        try:
            # 鏀堕泦鎵€鏈夋暟鎹?
            archive_data = {
                "metadata": metadata.to_dict(),
                "characters": [char.to_dict() for char in (self.get_characters(game_id) or [])],
                "story": self.get_story_progress(game_id),
                "save_data": self.load_game(game_id).to_dict() if self.load_game(game_id) else None,
                "exported_at": datetime.now().isoformat()
            }

            # 淇濆瓨鍒板綊妗ｇ洰褰?
            archive_path.write_text(json.dumps(archive_data, ensure_ascii=False, indent=2), encoding=Encoding.UTF8)

            logger.info(f"[GameMemoryManager] 瀵煎嚭瀛樻。: {archive_path}")
            return str(archive_path)

        except Exception as e:
            logger.error(f"[GameMemoryManager] 瀵煎嚭瀛樻。澶辫触: {e}")
            return None

    def import_archive(
        self,
        archive_path: str,
        target_group_id: Optional[int] = None,
        target_user_id: Optional[int] = None
    ) -> Optional[str]:
        """
        瀵煎叆娓告垙瀛樻。

        Args:
            archive_path: 褰掓。鏂囦欢璺緞
            target_group_id: 鐩爣缇ゅ彿(鍙€?
            target_user_id: 鐩爣鐢ㄦ埛鍙?鍙€?

        Returns:
            鏂扮殑娓告垙ID
        """
        archive_file = Path(archive_path)
        if not archive_file.exists():
            return None

        try:
            data = json.loads(archive_file.read_text(encoding=Encoding.UTF8))

            # 閲嶆柊鍒涘缓娓告垙
            game_id = self.create_game(
                game_name=data["metadata"]["game_name"],
                rule_system=data["metadata"]["rule_system"],
                mode_type=data["metadata"]["mode_type"],
                group_id=target_group_id,
                user_id=target_user_id,
                auto_save_enabled=data["metadata"].get("auto_save_enabled", True)
            )

            # 鎭㈠瑙掕壊鍗?
            if data.get("characters"):
                characters = [CharacterCard.from_dict(char) for char in data["characters"]]
                self._save_characters(game_id, characters)
                self._characters_cache[game_id] = characters

            # 鎭㈠鏁呬簨杩涘害
            if data.get("story"):
                self.update_story_progress(game_id, data["story"])

            # 鎭㈠瀛樻。
            if data.get("save_data"):
                game_dir = self._find_game_path(game_id)
                save_file = game_dir / "save_data.json"
                save_file.write_text(json.dumps(data["save_data"], ensure_ascii=False, indent=2), encoding=Encoding.UTF8)

            logger.info(f"[GameMemoryManager] 瀵煎叆瀛樻。: {game_id}")
            return game_id

        except Exception as e:
            logger.error(f"[GameMemoryManager] 瀵煎叆瀛樻。澶辫触: {e}")
            return None

    # ==================== Token浼扮畻宸ュ叿 (鏋舵瀯淇: 濮旀墭缁橳okenManager) ====================

    def estimate_tokens(self, text: str) -> int:
        """
        浼扮畻鏂囨湰鐨則oken鏁伴噺

        Args:
            text: 杈撳叆鏂囨湰

        Returns:
            token鏁伴噺
        """
        if self.token_manager:
            return self.token_manager.estimate_tokens(text)
        # 闄嶇骇浼扮畻
        return len(text) // 2 + len(text.split())

    def estimate_conversation_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        浼扮畻瀵硅瘽鍒楄〃鐨勬€籺oken鏁?

        Args:
            messages: 娑堟伅鍒楄〃 [{'role': 'user', 'content': '...'}, ...]

        Returns:
            鎬籺oken鏁?
        """
        if self.token_manager:
            return self.token_manager.estimate_conversation_tokens(messages)
        # 闄嶇骇浼扮畻
        total = 0
        for msg in messages:
            total += 10
            total += self.estimate_tokens(msg.get('content', ''))
        return total

    def estimate_conversation_history_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        浼扮畻瀵硅瘽鍘嗗彶鐨勬€籺oken鏁?鍏煎鏂规硶鍚?

        Args:
            messages: 娑堟伅鍒楄〃 [{'role': 'user', 'content': '...'}, ...]

        Returns:
            鎬籺oken鏁?
        """
        return self.estimate_conversation_tokens(messages)

    # ==================== 鏅鸿兘瀵硅瘽鍘嬬缉 ====================

    async def compress_old_messages(
        self,
        game_id: str,
        target_tokens: int = 80000,
        compression_ratio: float = 0.3
    ) -> bool:
        """
        鏅鸿兘鍘嬬缉鏃у璇濇秷鎭?

        鍘嬬缉绛栫暐:
        1. 淇濈暀鏈€杩戠殑娑堟伅(鐑暟鎹?
        2. 灏嗚緝鏃х殑娑堟伅鍘嬬缉鎴愭憳瑕?娓╂暟鎹?
        3. 淇濈暀鍏抽敭浜嬩欢鏍囪

        Args:
            game_id: 娓告垙ID
            target_tokens: 鐩爣token鏁?鐣欏嚭绌洪棿缁欏叾浠栧唴瀹?
            compression_ratio: 鍘嬬缉姣斾緥(鍘嬬缉澶氬皯鏃ф秷鎭?

        Returns:
            鏄惁鎴愬姛
        """
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return False

        conversation_file = game_dir / "conversation.json"
        if not conversation_file.exists():
            return False

        try:
            # 鍔犺浇鎵€鏈夋秷鎭?
            messages = json.loads(conversation_file.read_text(encoding=Encoding.UTF8))

            if len(messages) <= 20:
                # 娑堟伅鏁伴噺澶皯,涓嶉渶瑕佸帇缂?
                return True

            # 浼扮畻褰撳墠token鏁?
            current_tokens = self.estimate_conversation_tokens(messages)
            logger.info(f"[GameMemoryManager] 褰撳墠瀵硅瘽token鏁? {current_tokens}")

            if current_tokens <= target_tokens:
                # 鏈秴杩囬檺鍒?涓嶉渶瑕佸帇缂?
                return True

            # 璁＄畻闇€瑕佸帇缂╃殑娑堟伅鏁伴噺
            keep_messages = 15  # 淇濈暀鏈€杩?5鏉″畬鏁存秷鎭?
            compress_count = max(10, int(len(messages) * compression_ratio))

            # 鍒嗗壊娑堟伅
            to_compress = messages[:-keep_messages][-compress_count:]
            to_keep = messages[-keep_messages:]

            # 鐢熸垚鍘嬬缉鎽樿
            summary = await self._generate_summary(to_compress)

            # 鍒涘缓鎽樿鏉＄洰
            summary_message = {
                'role': 'system',
                'content': f"銆愬璇濇憳瑕?{to_compress[0].get('timestamp', '')} ~ {to_compress[-1].get('timestamp', '')})銆慭n{summary}",
                'timestamp': to_compress[-1].get('timestamp', ''),
                'is_summary': True
            }

            # 閲嶇粍娑堟伅: 淇濈暀鏇存棫鐨勬秷鎭?+ 鎽樿 + 淇濈暀鏈€杩戠殑娑堟伅
            very_old_messages = messages[:len(messages) - keep_messages - compress_count]
            new_messages = very_old_messages + [summary_message] + to_keep

            # 淇濆瓨鍘嬬缉鍚庣殑瀵硅瘽
            conversation_file.write_text(json.dumps(new_messages, ensure_ascii=False, indent=2), encoding=Encoding.UTF8)

            new_tokens = self.estimate_conversation_tokens(new_messages)
            logger.info(f"[GameMemoryManager] 瀵硅瘽鍘嬬缉瀹屾垚: {len(messages)} -> {len(new_messages)} 鏉℃秷鎭?)
            logger.info(f"[GameMemoryManager] Token鏁? {current_tokens} -> {new_tokens}")

            return True

        except Exception as e:
            logger.error(f"[GameMemoryManager] 鍘嬬缉瀵硅瘽澶辫触: {e}")
            return False

    async def _generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        鐢熸垚瀵硅瘽鎽樿

        Args:
            messages: 娑堟伅鍒楄〃

        Returns:
            鎽樿鏂囨湰
        """
        # 鎻愬彇瀵硅瘽鍐呭
        dialogue = []
        for msg in messages:
            role_name = "鐜╁" if msg.get('role') == 'user' else "KP(寮ュ▍)"
            dialogue.append(f"{role_name}: {msg.get('content', '')}")

        dialogue_text = "\n".join(dialogue)

        # 绠€鍗曠殑鍏抽敭璇嶆憳瑕?閬垮厤棰濆鐨凙I璋冪敤)
        # 注意: 后续可以接入AI生成更智能的摘要
        summary_lines = []

        # 鎻愬彇鍏抽敭淇℃伅
        if "妫€瀹? in dialogue_text or "鍒ゅ畾" in dialogue_text:
            summary_lines.append("鈥?杩涜浜嗗椤规瀹氬垽瀹?)
        if "鎴樻枟" in dialogue_text or "鏀诲嚮" in dialogue_text:
            summary_lines.append("鈥?鍙戠敓浜嗘垬鏂楀啿绐?)
        if "鎺㈢储" in dialogue_text or "璋冩煡" in dialogue_text:
            summary_lines.append("鈥?杩涜浜嗗満鏅帰绱㈠拰璋冩煡")
        if "楠板瓙" in dialogue_text or "鎶曟幏" in dialogue_text:
            summary_lines.append("鈥?杩涜浜嗛殢鏈烘姇鎺?)

        # 鎻愬彇瑙掕壊琛屽姩
        user_actions = [msg for msg in messages if msg.get('role') == 'user']
        if user_actions:
            summary_lines.append(f"鈥?鐜╁杩涜浜唟len(user_actions)}娆¤鍔?)

        # 缁熻KP鍥炲
        kp_responses = [msg for msg in messages if msg.get('role') == 'assistant']
        if kp_responses:
            summary_lines.append(f"鈥?KP杩涜浜唟len(kp_responses)}娆℃弿杩板拰鍥炲簲")

        if not summary_lines:
            summary_lines.append("鈥?杩涜浜嗗父瑙勫璇濅氦浜?)

        return "\n".join(summary_lines)

    # ==================== 瀵硅瘽鍘嗗彶绠＄悊(浼樺寲鐗? ====================

    def add_conversation_message(
        self,
        game_id: str,
        role: str,  # 'user' or 'assistant'
        content: str,
        player_id: Optional[int] = None,
        player_name: Optional[str] = None
    ) -> bool:
        """
        娣诲姞娓告垙瀵硅瘽娑堟伅

        Args:
            game_id: 娓告垙ID
            role: 瑙掕壊 ('user' or 'assistant')
            content: 娑堟伅鍐呭
            player_id: 鐜╁ID (user娑堟伅鏃?
            player_name: 鐜╁鍚嶇О (user娑堟伅鏃?

        Returns:
            鏄惁鎴愬姛
        """
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return False

        conversation_file = game_dir / "conversation.json"

        try:
            # 鍔犺浇鐜版湁瀵硅瘽
            messages = []
            if conversation_file.exists():
                messages = json.loads(conversation_file.read_text(encoding=Encoding.UTF8))

            # 娣诲姞鏂版秷鎭?
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            if role == 'user':
                message['player_id'] = player_id
                message['player_name'] = player_name

            messages.append(message)

            # Token鎰熺煡鐨勯檺鍒? 涓嶆槸绠€鍗曢檺鍒舵潯鏁?鑰屾槸浼扮畻token鏁?
            max_tokens = 100000  # 鎬籺oken闄愬埗(鐣欏嚭31072缁欏叾浠栧唴瀹?
            current_tokens = self.estimate_conversation_tokens(messages)

            if current_tokens > max_tokens:
                # 瓒呰繃闄愬埗,瑙﹀彂鍘嬬缉
                logger.warning(f"[GameMemoryManager] 瀵硅瘽token鏁?{current_tokens} 瓒呰繃闄愬埗 {max_tokens}")
                # 绉婚櫎鏈€鏃х殑闈炴憳瑕佹秷鎭?淇濈暀鎽樿)
                new_messages = []
                removed_count = 0
                for msg in messages:
                    if msg.get('is_summary'):
                        new_messages.append(msg)
                    elif len(new_messages) >= 40:  # 淇濈暀鏈€杩?0鏉″畬鏁存秷鎭?
                        removed_count += 1
                    else:
                        new_messages.append(msg)
                messages = new_messages
                logger.info(f"[GameMemoryManager] 绉婚櫎浜?{removed_count} 鏉℃棫娑堟伅浠ユ帶鍒秚oken鏁?)

            # 淇濆瓨
            conversation_file.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding=Encoding.UTF8)
            logger.debug(f"[GameMemoryManager] 娣诲姞瀵硅瘽娑堟伅: {game_id}, role={role}, total_messages={len(messages)}")
            return True
        except Exception as e:
            logger.error(f"[GameMemoryManager] 娣诲姞瀵硅瘽娑堟伅澶辫触: {e}")
            return False

    def get_conversation_history(
        self,
        game_id: str,
        max_tokens: int = 80000
    ) -> List[Dict[str, str]]:
        """
        鑾峰彇娓告垙瀵硅瘽鍘嗗彶(Token鎰熺煡鐗堟湰)

        Args:
            game_id: 娓告垙ID
            max_tokens: 鏈€澶oken鏁?鐣欏嚭绌洪棿缁欏叾浠栧唴瀹?

        Returns:
            娑堟伅鍒楄〃 [{'role': 'user', 'content': '...'}, ...]
        """
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return []

        conversation_file = game_dir / "conversation.json"
        if not conversation_file.exists():
            return []

        try:
            messages = json.loads(conversation_file.read_text(encoding=Encoding.UTF8))

            # Token鎰熺煡鐨勯€夋嫨: 浠庢渶鏂板紑濮嬬疮鍔?鐩村埌鎺ヨ繎token闄愬埗
            result = []
            total_tokens = 0

            # 鍏堜繚鐣欐憳瑕?绯荤粺娑堟伅)
            summaries = [msg for msg in messages if msg.get('is_summary')]
            for summary in summaries:
                summary_tokens = self.estimate_tokens(summary.get('content', ''))
                if total_tokens + summary_tokens <= max_tokens:
                    result.append({
                        'role': summary['role'],
                        'content': summary['content']
                    })
                    total_tokens += summary_tokens

            # 鍐嶆坊鍔犳渶鏂版秷鎭?鍊掑簭閬嶅巻)
            recent_messages = [msg for msg in messages if not msg.get('is_summary')]
            for msg in reversed(recent_messages):
                msg_tokens = 10 + self.estimate_tokens(msg.get('content', ''))  # 10鏄鑹叉爣璁皌oken
                if total_tokens + msg_tokens <= max_tokens:
                    result.insert(len([s for s in result if not s['role'] == 'system']), {
                        'role': msg['role'],
                        'content': msg['content']
                    })
                    total_tokens += msg_tokens
                else:
                    break

            logger.debug(f"[GameMemoryManager] 鑾峰彇瀵硅瘽鍘嗗彶: {game_id}, count={len(result)}, tokens={total_tokens}")
            return result
        except Exception as e:
            logger.error(f"[GameMemoryManager] 鑾峰彇瀵硅瘽鍘嗗彶澶辫触: {e}")
            return []

    # ==================== 杈呭姪鏂规硶 ====================

    def _find_game_path(self, game_id: str) -> Path:
        """鏌ユ壘娓告垙鐩綍"""
        # 鍏堝湪缇ょ洰褰曚腑鏌ユ壘
        groups_dir = self.base_path / "groups"
        if groups_dir.exists():
            for group_path in groups_dir.iterdir():
                game_path = group_path / "games" / game_id
                if game_path.exists():
                    return game_path

        # 鍐嶅湪鐢ㄦ埛鐩綍涓煡鎵?
        users_dir = self.base_path / "users"
        if users_dir.exists():
            for user_path in users_dir.iterdir():
                game_path = user_path / "games" / game_id
                if game_path.exists():
                    return game_path

        # 杩斿洖绌鸿矾寰?
        return self.base_path / "temp" / game_id

    def _save_metadata(self, metadata: GameMetadata, game_dir: Path):
        """淇濆瓨鍏冩暟鎹?""
        meta_file = game_dir / "meta.json"
        meta_file.write_text(json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2), encoding=Encoding.UTF8)

    def _save_characters(self, game_id: str, characters: List[CharacterCard]):
        """淇濆瓨瑙掕壊鍗?""
        game_dir = self._find_game_path(game_id)
        characters_file = game_dir / "characters.json"
        characters_file.write_text(
            json.dumps([char.to_dict() for char in characters], ensure_ascii=False, indent=2),
            encoding=Encoding.UTF8
        )
        self._characters_cache[game_id] = characters

    def clear_conversation_history(self, game_id: str) -> bool:
        """
        娓呯┖瀵硅瘽鍘嗗彶

        Args:
            game_id: 娓告垙ID

        Returns:
            鏄惁鎴愬姛
        """
        game_dir = self._find_game_path(game_id)
        if not game_dir.exists():
            return False

        conversation_file = game_dir / "conversation.json"
        try:
            if conversation_file.exists():
                conversation_file.unlink()
            logger.info(f"[GameMemoryManager] 娓呯┖瀵硅瘽鍘嗗彶: {game_id}")
            return True
        except Exception as e:
            logger.error(f"[GameMemoryManager] 娓呯┖瀵硅瘽鍘嗗彶澶辫触: {e}")
            return False


# 鍏ㄥ眬鍗曚緥
_game_memory_manager = None


def get_game_memory_manager() -> GameMemoryManager:
    """鑾峰彇娓告垙璁板繂绠＄悊鍣ㄥ崟渚?""
    global _game_memory_manager
    if _game_memory_manager is None:
        _game_memory_manager = GameMemoryManager()
    return _game_memory_manager
