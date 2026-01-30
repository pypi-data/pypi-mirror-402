<?php

declare(strict_types=1);

namespace core\handler;

use Exception;
use utils\CommandInterface;

final class AddEventListenerHandler extends AbstractHandler
{
    function process(CommandInterface $command): void
    {
        throw new Exception(__CLASS__ . ' is not implemented in PHP');
    }
}
