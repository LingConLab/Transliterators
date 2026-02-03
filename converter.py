import re, os, csv

current_folder = os.path.dirname(os.path.abspath(__file__))
ortho_table_path = os.path.join(current_folder, os.path.join("static", "ortho_table.csv"))
ortho_txt_default_name = "ortho"

all_letters = "A-Za-zÀ-ÖØ-öø-ӿԀ-ԯⷩ"
punct = "\!-/:-@\[-`{-~ -¿\‐-⁞"

#cyr_check = "[ПпБДдЛлЖжШшЩщФфЦцЧчИиЙйЬьЪъЫыЭэЮюЯя]"
#lat_check = "[SsVvFfIiGgZzQqNR]"

_cyr = ["cyr", "cyrillic", "кир", "кириллица"]
#_lat = ["lat", "latin", "лат", "латиница"]
other_targets = ["ipa", "cauc"]

possible_targets = _cyr + other_targets
recommended_targets = [_cyr[0]] + other_targets


def raise_error_wrong_argument(token, recommended):
    raise ValueError(f"Invalid '{token}' argument given! Should be one of these: {recommended}")


class ConverterOutput:
    """The output of the Converter.convert() function."""
    
    def __init__(self, text, lang, orig, target):
        """
        Parameters
        ----------
        """
        
        self.text = text
        self.lang = lang
        self.orig = orig
        self.target = target


    def __repr__(self):
        return self.text


    def full(self):
        """Prints all the settings of the converted text."""
        return f"ConverterOutput(\n\ttext='{self.text}',\n\tlang={self.lang}, orig={self.orig}, target={self.target}\n)"


class Converter:
    """The main class to convert from alphabet X to alphabet Y.

    Make a `Converter` object. Optionally, set the default target alphabet as an argument:
    > c = Converter(target="cyr")
    
    Then use the method `convert` to change the alphabet of a text:
    > converted_text = c.convert(original_text)
    """
    
    def __init__(self, lang, orig=None, target=None):
        """
        Parameters
        ----------
        """
        
        with open(ortho_table_path, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f, delimiter=","))
            self._ortho_table = {}
            headers = []
            for i in range(len(reader)):
                row = reader[i]
                if i == 0:
                    headers = row
                else:
                    self._ortho_table[row[0]] = {
                        headers[i]: row[i] for i in range(1, len(row))}
        
        possible_langs = sorted(set([x.split("_")[0] for x in list(list(self._ortho_table.values())[0].keys())]))
        if lang in possible_langs:
            self.lang = lang
        else:
            raise_error_wrong_argument("lang", possible_langs)

        if orig in possible_targets:
            self.orig = orig
        elif orig is None:
            self.orig = None
        else:
            raise_error_wrong_argument("orig", recommended_targets)

        if target in _cyr:
            self._lang_target = f"{self.lang}_{_cyr[0]}"
        elif target in other_targets:
            self._lang_target = f"{self.lang}_{target}"
        elif target is None:
            self._lang_target = None
        else:
            raise_error_wrong_argument("target", recommended_targets)
        
        self.target = target
        
        with open(
            os.path.join(current_folder, os.path.join("static", f"ortho_{lang}.txt")),
            "r", encoding="utf-8-sig") as file:
            ortho_txt_file = file.readlines()
        
        self._ortho_to_meta = {}
        for line in ortho_txt_file:
            if not line.startswith("#"):
                bad, good = line.split("\t")
                good = good.strip("\r\n")
                self._ortho_to_meta[bad] = good


    def __repr__(self):
        return f"Converter(lang={self.lang}, orig={self.orig}, target={self.target})"


    def convert(self, text, orig=None, target=None):
        """
        Converts a text.
        
        Parameters
        ----------
        """
        if text is None:
            return None
        if orig is None:
            if self.orig is None:
                raise ValueError("No 'orig' value given!")
            else:
                orig = self.orig
        elif orig not in possible_targets:
            raise_error_wrong_argument("orig", recommended_targets)
        
        lang_target = None
        if target is None:
            if self._lang_target is None:
                raise ValueError("No 'target' value given!")
            else:
                lang_target = self._lang_target
                target = self.target
        elif target in possible_targets:
            lang_target = f"{self.lang}_{target}"
        else:
            raise_error_wrong_argument("target", recommended_targets)
        
        ######################

        # Fix palochkas which are incorrectly capital but within a word
        text = re.sub(f"(?<=[{all_letters}])Ӏ", "ӏ", text)

        # Fix palochkas which are written as '1' or '|'
        text = re.sub(f"(?<=[{all_letters}])[|1]|[|1](?=[{all_letters}])", "ӏ", text)

        # Split into tokens
        tokens = re.findall(f"[{all_letters}]+|[{punct}]+|[0-9]+|[^{all_letters}{punct}0-9]+", text)

        # Convert to the meta-orthography
        for i in range(len(tokens)):
            if re.fullmatch(f"[{all_letters}]+", tokens[i]):
                for bad, good in self._ortho_to_meta.items():
                    tokens[i] = re.sub(bad, good, tokens[i])
        text = "".join(tokens)

        # Convert to the target orthography
        for letter in self._ortho_table:
            text = re.sub(letter, self._ortho_table[letter][lang_target], text)
        
        return ConverterOutput(text, lang=self.lang, orig=orig, target=target)

