# MIT License
# 
# Copyright (c) 2026 andshrew
# https://github.com/andshrew/DOOM3-BFG-Profile
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Config_Item:
  name: Optional[bytes] = b'\x00'
  value: Optional[bytes] = b'\x00'
  is_empty: bool = True
  is_invalid: bool = False

  def __init__(self, name=None, value=None):
    """
    Create a new Config Item object

    :param name: Name of the config item
    :param value: Value of the config item
    """
    if isinstance(name, str) or isinstance(name, bytes):
      self.set_name(name)
    if isinstance(value, str) or isinstance(value, bytes):
      self.set_value(value)

  def get_name(self):
    """
    Returns the name as a string
    """
    if not self.is_invalid:
      return self.name.decode()
  
  def get_value(self):
    """
    Returns the value as a string
    """
    if not self.is_invalid:
      return self.value.decode()
  
  def set_name(self, value):
    """
    Set the config items name, automatically null terminates

    :param value: Config item name as string or bytes
    """
    if isinstance(value, str):
      value = value.encode()
    if isinstance(value, bytes):
      if value[-1:] != b'\x00':
        value = value + b'\x00'
      self.name = value
      self._check_invalid()
      self._check_empty()

  def set_value(self, value):
    """
    Set the config items value, automatically null terminates
    
    :param value: Config item value as string or bytes
    """
    if isinstance(value, str):
      value = value.encode()
    if isinstance(value, bytes):
      if value[-1:] != b'\x00':
        value = value + b'\x00'
      self.value = value
      self._check_invalid()
      self._check_empty()

  def _check_invalid(self):
    """
    Test if items name and value can decode into a string

    On failure is_invalid set to True
    """
    try:
      self.name.decode()
      self.value.decode()
      self.is_invalid = False
    except Exception as ex:
      logger.debug(print(f'Config Item invalid: {ex.args} {ex.__class__}'))
      self.is_invalid = True

  def _check_empty(self):
    """
    Test if both the items name and value are null

    is_empty set based on result
    """
    if self.name == b'\x00' and self.value == b'\x00':
      self.is_empty = True
    else:
      self.is_empty = False

@dataclass 
class BFG_Profile:
  file_path: str
  checksum_1: Optional[bytes] = b''
  checksum_2: Optional[bytes] = b''
  header: Optional[bytes] = b''
  data: Optional[bytes] = b''
  config: List[Config_Item] = field(default_factory=list)
  total_config_items: Optional[bytes] = b''
  additional_data: Optional[bytes] = b''
  is_parsed: bool = False

  CONFIG_HEADER = bytes.fromhex('80 94 CC A1 04')
  CONFIG_FOOTER = bytes.fromhex('00' * 17 + 'C8 01')
  CONFIG_PADDING = bytes.fromhex('00' * 205 + '01')

  def __init__(self, file_path, new_profile=False):
    """
    Create a new DOOM 3 BFG Profile object. Parse the contents when loading 
    an existing profile.bin

    :param file_path: Path to an existing profile.bin to parse
    :param new_profile: True to create a blank profile. file_path is not loaded
    """
    self.config = []
    self.file_path = file_path
    if new_profile:
      # Create a new profile
      self.is_parsed = True
      return
    
    # Load and parse an existing profile.bin file
    try:
      with open(self.file_path, 'rb') as f:
        self.checksum_1 = f.read(4)
        self.checksum_2 = f.read(4)
        header = f.read(5)
        self.header = header
        if header != self.CONFIG_HEADER:
          raise ValueError(f'File header \'{format_bytes(header)}\' is not the expected value of \'{format_bytes(self.CONFIG_HEADER)}\'')
        self.data = f.read()
        if not self.validate_checksums():
          raise ValueError(f'File checksum is not the expected value')
        self.parse_profile()
        if not self.is_parsed:
          raise KeyError(f'File has not parsed successfully')
    except FileNotFoundError:
      print(f'Profile file {self.file_path} not found')
    except Exception as ex:
      print(f'Error: {ex.args} {ex.__class__}')

  def validate_checksums(self):
    """
    Validate that both checksums in the loaded profile.bin are accurate for the
    data that has been read from the file
    """
    checksum_1_validated = False
    checksum_2_validated = False
    if self.checksum_2 == MD5_BlockChecksum(self.header + self.data):
      checksum_2_validated = True
    if self.checksum_1 == MD5_BlockChecksum(self.checksum_2 + self.header + self.data):
      checksum_1_validated = True
    if checksum_1_validated == checksum_2_validated == True:
      logger.debug(f'Checksums validated Checksum1: {format_bytes(self.checksum_1)} Checksum2: {format_bytes(self.checksum_2)}')
      return True
    return False

  def get_config_item_count(self):
    """
    Returns the config item count from the loaded profile.bin
    """
    return int.from_bytes(self.total_config_items, byteorder='little')
  
  def _update_config_item_count(self):
    """
    Returns the current config item count as a single byte
    """
    config_count = sum(1 for c in self.config if c.is_empty == False)
    if config_count > 255:
      logger.error(f'Too many config items in list: {config_count}. Only first 255 will be included')
      config_count = 255
    return config_count.to_bytes(1, byteorder='little')
  
  def add_config_item(self, item, position=-1):
    """
    Add a new config item. If an item with the same name already exists then the
    existing item value is changed

    :param item: Config_Item object to add
    :param position: Add the item to a specific position in the list
    """
    if not isinstance(item, Config_Item):
      return False
    
    if self.change_config_item(name=item.get_name(), value=item.get_value()):
      # This item already exists and has been updated
      logger.debug(f'{item.get_name()} already exists and the value has been updated: {item.get_value()}')
      return True
    
    if position >= 0:
      self.config.insert(position, item)
      logger.debug(f'{item.get_name()} value: {item.get_value()} inserted at position {position}')
      return True
    else:
      empty_index = next((i for i, item in enumerate(self.config) if item.is_empty == True and item.is_invalid == False), -1)
      if empty_index > 0:
        # If there are empty items in the list then insert prior to the first empty item
        self.config.insert(empty_index, item)
      else:
        self.config.append(item)
      logger.debug(f'{item.get_name()} value: {item.get_value()} has been added')
      return True
  
  def change_config_item(self, name, value):
    """
    Change the value of a config item. Does nothing if the item does not exist

    :param name: Name of the config item to change
    :param value: Value of the config item
    """

    exists_index = next((
      i for i, item in enumerate(self.config)
        if not item.is_invalid
          if name.lower() in item.get_name().lower()
    ), -1)
    if exists_index >= 0:
      self.config[exists_index].set_value(value)
      return True
    return False
  
  def remove_config_item(self, name):
    """
    Removes the specified config item

    :param name: Name of the config item to remove
    """
    found = False
    searching = True
    while searching:
      exists_index = next((
        i for i, item in enumerate(self.config)
          if not item.is_invalid
            if name.lower() in item.get_name().lower()
      ), -1)
      if exists_index >= 0:
        found = True
        self.config.pop(exists_index)
      else:
        searching = False
      
    if found:
      return True
    else: return False
  
  def print_config_items(self):
    """
    Print all config items
    """
    for item in self.config:
      msg = f'Name: {item.get_name()} Value: {item.get_value()}'
      if item.is_invalid or item.is_empty:
        msg = msg + f' | Empty: {item.is_empty} Invalid: {item.is_invalid})'
      print(msg)
  
  def parse_profile(self):
    """
    Parse the contents of the profile.bin loaded in the data attribute
    """
    if not isinstance(self.data, bytes):
      logger.error('The objects data atribute should contain the profile file bytes before attempting to parse the profile')
      return
    if isinstance(self.data, bytes):
      with io.BytesIO(self.data) as b:
        self.total_config_items = b.read(1)
        name = b''
        value = b''
        is_value = False
        config_count = self.get_config_item_count()
        while config_count > len(self.config):
          # Read from the buffer 1 byte at a time
          # When NULL is read, switch between config item name and value
          # Repeat until the expected number of config items have been found
          read = b.read(1)
          if read == b'':
            logger.error('Seemingly reached the end of the ReadableBuffer before finding all config items')
            logger.error(f'Expected items: {config_count}, found items: {len(self.config)}')
            break
          if is_value:
            value = value + read
          else:
            name = name + read
          if read == b'\x00':
            if not is_value:
              # Switch to item value
              is_value = True
              continue
            else:
              # A complete config item has been found, append to the object
              self.config.append(Config_Item(name, value))
              # Switch back to item name
              is_value = False
              name = value = b''
        footer = b.read(19)
        if footer == self.CONFIG_FOOTER:
          logger.debug(f'The config footer matches the expected value: {format_bytes(self.CONFIG_FOOTER)}')
        elif footer[-3:] == self.CONFIG_FOOTER[-3:]:
          logger.warning(f'The config footer does NOT match the expected value, but the last three bytes do:')
          logger.warning(f'Actual: {format_bytes(footer)}')
          logger.warning(f'Expected: {format_bytes(self.CONFIG_FOOTER)}')
          logger.warning(f'Subsituting actual footer for the expected value')
          footer = self.CONFIG_FOOTER
        padding = b.read(206)
        if padding == self.CONFIG_PADDING:
          logger.debug(f'The profile padding matches the expected value: {format_bytes(self.CONFIG_PADDING)}')
        if b.tell() != len(self.data):
          logger.info('Additional data exists after the main config data')
          self.additional_data = b.read()
        if footer == self.CONFIG_FOOTER and padding == self.CONFIG_PADDING:
          logger.debug('Both the config footer and padding match the expected values')
          self.is_parsed = True
  
  def generate_profile(self, output_path='profile.bin'):
    if not self.is_parsed:
      logger.error('The object must be in a parsed state before a profile file can be generated')
      return
    # Assemble the contents of the new profile.bin file
    profile = self.CONFIG_HEADER
    profile = profile + self._update_config_item_count()
    for item in self.config:
      profile = profile + item.name + item.value
    profile = profile + self.CONFIG_FOOTER
    profile = profile + self.CONFIG_PADDING
    profile = profile + self.additional_data
    # Calculate the new checksums and prepend them
    checksum_2 = MD5_BlockChecksum(profile)
    profile = checksum_2 + profile
    checksum_1 = MD5_BlockChecksum(profile)
    profile = checksum_1 + profile
    try:
      with open(output_path, 'wb') as f:
        f.write(io.BytesIO(profile).read())
        logger.debug(f'Profile file written to: {output_path}')
    except Exception as ex:
      logger.error(f'Profile destination path: {output_path}')
      logger.error(f'Unable to write profile file: {ex.args} {ex.__class__}')

def MD5_BlockChecksum(data):
  """
  Calculate the MD5-based checksum of the profile.bin data
  
  Returns 4 bytes in big endian order

  :param data: Bytes of the data to be hashed
  """
  # Calculates the MD5 checksum of the profile file
  # Returns 4 bytes in big endian order
  if not isinstance(data, bytes):
    logger.error('Input must be bytes')

  # Calculate the MD5 hash of the data
  md5_hash = hashlib.md5(data)
  md5_digest = md5_hash.digest()

  # Extract values from the MD5 digest and combine them as per the DOOM 3 BFG code
  # https://github.com/id-Software/DOOM-3-BFG/blob/1caba1979589971b5ed44e315d9ead30b278d8b4/neo/idlib/hashing/MD5.cpp#L298
  val = (
    (md5_digest[3] << 24 | md5_digest[2] << 16 | md5_digest[1] << 8 | md5_digest[0]) ^
    (md5_digest[7] << 24 | md5_digest[6] << 16 | md5_digest[5] << 8 | md5_digest[4]) ^
    (md5_digest[11] << 24 | md5_digest[10] << 16 | md5_digest[9] << 8 | md5_digest[8]) ^
    (md5_digest[15] << 24 | md5_digest[14] << 16 | md5_digest[13] << 8 | md5_digest[12])
  )
  result = val.to_bytes(4, byteorder='big') 
  logger.debug(f'Checksum result: {format_bytes(result)}')
  return result

def format_bytes(data):
  """
  Format bytes as space seperated hex string ('00 01 02')
  
  :param data: Bytes to be formatted
  """
  if not isinstance(data, bytes):
    return
  return data.hex(' ', 1).upper()

logger = logging.getLogger(__name__)