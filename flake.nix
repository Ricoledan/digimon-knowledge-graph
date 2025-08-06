{
  description = "Digimon Knowledge Graph Project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonPackages = ps: with ps; [
          # Web Scraping
          beautifulsoup4
          requests
          aiohttp
          lxml
          
          # Translation
          googletrans
          deep-translator
          
          # Data Processing
          pandas
          numpy
          spacy
          
          # Graph Database
          neo4j
          py2neo
          
          # Analysis & Visualization
          networkx
          matplotlib
          seaborn
          plotly
          
          # Utilities
          python-dotenv
          pyyaml
          tqdm
          loguru
          tenacity
          
          # Image Processing
          pillow
          
          # Development
          pytest
          pytest-asyncio
          ipykernel
          jupyter
          black
          ipython
        ];
        
        pythonEnv = pkgs.python311.withPackages pythonPackages;
        
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            
            # Additional tools
            docker-compose
            neo4j
            git
            curl
            jq
            
            # Node.js for any web visualizations
            nodejs_20
            
            # Database tools
            cypher-shell
          ];
          
          shellHook = ''
            echo "🦖 Digimon Knowledge Graph Development Environment"
            echo "Python: $(python --version)"
            echo "Neo4j: $(neo4j --version 2>/dev/null || echo 'Use docker-compose')"
            echo ""
            echo "Quick start:"
            echo "  docker-compose up -d    # Start Neo4j"
            echo "  python -m pytest        # Run tests"
            echo "  jupyter notebook        # Start Jupyter"
            echo ""
            
            # Create .env file if it doesn't exist
            if [ ! -f .env ]; then
              cp .env.example .env
              echo "Created .env file from template"
            fi
            
            # Set up Python path
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
          '';
        };
      });
}