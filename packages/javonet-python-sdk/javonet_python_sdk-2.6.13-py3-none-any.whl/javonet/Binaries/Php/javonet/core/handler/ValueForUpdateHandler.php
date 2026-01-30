<?php

declare(strict_types=1);

namespace core\handler;

use Exception;
use utils\CommandInterface;

final class ValueForUpdateHandler extends AbstractHandler
{
    /**
     * @throws Exception
     */
    public function process(CommandInterface $command)
    {
        throw new Exception(__CLASS__ . ' is not implemented in PHP');
    }
}

