require_relative 'abstract_command_handler'
require_relative '../reference_cache/references_cache'

class DestructReferenceHandler < AbstractCommandHandler
  def initialize
    @required_parameters_count = 1
  end

  def process(command)
    begin
      if command.payload.length == @required_parameters_count
        reference_id = payload[0]
        return false if reference_id.nil? || !reference_id.is_a?(String)

        ReferencesCache.instance.delete_reference(reference_id)
      else
        return false
      end
    rescue Exception => e
      return e
    end
  end
end
