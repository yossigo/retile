# retile
<img src="https://cdn.pastemagazine.com/www/articles/BEST-BENDER-quotes-futurama.jpg"/>

_Inspired by [Tile replicator](https://github.com/pivotal-cf/replicator)_

Retile takes a [Redis Enterprise for PCF tile](https://network.pivotal.io/products/redis-enterprise-pack) and creates a new one with an added label, thus making it different from the unmutated tile and capable of being installed side by side.  This can allow operators to create different clusters for different business units, each with their own settings.

## Requirements
- python
- tar
- zip
- a tile you wish to mutate

## Usage

To install dependancies, run `pip install -r requirements.txt`.

To mutate a tile, run `python retile.py <tile file> <label>`

## Installing the mutated tile

Once mutated, upload the tile to your Ops Manager.

Under Routing, ensure that the domains and ports do not collide with other installations of the tile.

Once installed, run `cf enable-service-access redislabs-<label>` to enable the new service in your foundation

