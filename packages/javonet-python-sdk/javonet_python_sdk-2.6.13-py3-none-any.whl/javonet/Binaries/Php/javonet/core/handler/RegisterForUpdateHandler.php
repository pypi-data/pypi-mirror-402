<?php

declare(strict_types=1);

namespace core\handler;

use utils\CommandInterface;
use utils\exception\JavonetArgumentsMismatchException;
use utils\Uuid;

/**
 * Registers an object in a per\-thread\-/process context dictionary so it can be returned
 * as VALUE_FOR_UPDATE entries in response payloads.
 */
final class RegisterForUpdateHandler extends AbstractHandler
{
    /** Minimal number of required payload items: [objectToRegister, optionalGuid] */
    private const REQUIRED_PARAMETERS_COUNT = 2;

    /**
     * Thread\-local emulation: key \= thread/process ID, value \= [uuid => mixed]
     * @var array<string,array<string,mixed>>
     */
    public static array $invocationContexts = [];

    /**
     * Registers the provided object under a UUID in the current context.
     * If a valid UUID string is provided as the second payload item, it is used;
     * otherwise a new UUID v4 is generated.
     *
     * @param CommandInterface $command Payload: [objectToRegister, optionalGuid]
     * @return mixed The registered object.
     */
    public function process(CommandInterface $command)
    {
        $payload = $command->getPayload();

        if (count($payload) < self::REQUIRED_PARAMETERS_COUNT) {
            throw new JavonetArgumentsMismatchException(self::class, self::REQUIRED_PARAMETERS_COUNT);
        }

        $objectToRegister = $payload[0];
        $guidToRegister = Uuid::uuid4()->toString();

        if (isset($payload[1]) && is_string($payload[1])) {
            $guidToRegister = strtolower($payload[1]);
        }

        $contextDictionary =& self::getOrCreateContextDictionary();
        if (!array_key_exists($guidToRegister, $contextDictionary)) {
            $contextDictionary[$guidToRegister] = $objectToRegister;
        }

        return $objectToRegister;
    }

    /**
     * @return array<string,mixed>
     */
    private static function &getOrCreateContextDictionary(): array
    {
        $key = (string) getmypid();
        if (!isset(self::$invocationContexts[$key])) {
            self::$invocationContexts[$key] = [];
        }
        return self::$invocationContexts[$key];
    }
}
