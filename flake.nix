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
          lxml
          
          # Data Processing
          pandas
          numpy
          
          # Graph Database
          neo4j
          
          # Analysis & Visualization
          networkx
          matplotlib
          
          # Utilities
          python-dotenv
          pyyaml
          tqdm
          
          # Image Processing
          pillow
          
          # Development
          pytest
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
            
            # Database tools (cypher-shell is included with neo4j)
          ];
          
          shellHook = ''
            echo "🦖 Digimon Knowledge Graph Development Environment"
            echo "Python: $(python --version)"
            echo "Neo4j: $(neo4j --version 2>/dev/null || echo 'Use docker-compose')"
            echo ""
            echo "Installing additional Python packages from requirements.txt..."
            echo ""
            
            # Create virtual environment if it doesn't exist
            if [ ! -d .venv ]; then
              echo "Creating Python virtual environment..."
              python -m venv .venv
            fi
            
            # Activate virtual environment
            source .venv/bin/activate
            
            # Install packages from requirements.txt
            pip install -r requirements.txt --quiet
            
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