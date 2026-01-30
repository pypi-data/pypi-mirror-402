require 'ffi'
require 'os'
require_relative 'transmitter_wrapper'

class Transmitter

  def self.send_command(message_byte_array, message_byte_array_len)
    message = FFI::MemoryPointer.new(:uchar, message_byte_array_len, true)
    message.put_array_of_uchar(0, message_byte_array)

    response_len = TransmitterWrapper.SendCommand(message, message_byte_array_len)

    if response_len.positive?
      response = FFI::MemoryPointer.new(:uchar, response_len, true)
      response.put_uchar(0, message.get_uchar(0))
      TransmitterWrapper.ReadResponse(response, response_len)
      response.get_array_of_uchar(0, response_len)
    elsif response_len.zero?
      raise RuntimeError, "Response is empty"
    else
      error_message = get_native_error
      raise RuntimeError, "Javonet native error code: #{response_len}. #{error_message}"
    end
  end


  def self.activate(license_key)
    activation_result = TransmitterWrapper.Activate(license_key)
    if activation_result < 0
      error_message = get_native_error
      raise Exception.new "Javonet activation result: " + activation_result.to_s + ". Native error message: " + error_message
    else
      return activation_result
    end
  end

  def self.get_native_error
    TransmitterWrapper.GetNativeError
  end

  def self.set_config_source(config_path)
    set_config_result = TransmitterWrapper.SetConfigSource(config_path)
    if set_config_result < 0
      error_message = get_native_error
      raise Exception.new "Javonet set config source result: " + set_config_result.to_s + ". Native error message: " + error_message
    else
      return set_config_result
    end
  end

  def self.set_javonet_working_directory(config_path)
    set_working_directory_result = TransmitterWrapper.SetWorkingDirectory(config_path)
    if set_working_directory_result < 0
      error_message = get_native_error
      raise Exception.new "Javonet set working directory result: " + set_working_directory_result.to_s + ". Native error message: " + error_message
    else
      return set_working_directory_result
    end
  end
end
