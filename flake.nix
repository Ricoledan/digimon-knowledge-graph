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
            echo "Digimon Knowledge Graph Development Environment"
            echo "Python: $(python --version)"
            echo "Neo4j: $(neo4j --version 2>/dev/null || echo 'Use docker-compose')"
            
            # Create virtual environment if it doesn't exist
            if [ ! -d .venv ]; then
              echo "Creating Python virtual environment..."
              python -m venv .venv
              echo "Run 'source .venv/bin/activate && pip install -r requirements.txt' to install dependencies"
            else
              # Just activate the venv, don't install every time
              source .venv/bin/activate
            fi
            
            # Create .env file if it doesn't exist
            if [ ! -f .env ] && [ -f .env.example ]; then
              cp .env.example .env
              echo "Created .env file from template"
            fi
            
            # Set up Python path
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            
            echo ""
            echo "Quick start:"
            echo "  ygg start               # Start Neo4j"
            echo "  ygg status              # Check pipeline status"
            echo "  jupyter notebook        # Start Jupyter"
          '';
        };
      });
}