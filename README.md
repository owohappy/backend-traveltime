# taveltime

A App that rewards you for taking the bus instead of the car 

## Prerequisites

Ensure you have the following installed:
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Getting Started

Follow these steps to set up and run the project locally.

### Clone the Repository

```bash
git clone https://github.com/owohappy/traveltime-backend.git
cd traveltime-backend
```

### Build and Start the Containers

```bash
docker-compose up --build
```

### Access the Application

- The application will be available at `http://localhost:8000` (Port can be changed in the server config).

## Project Structure
TODO

- **docker-compose.yml**: Defines the services and their configurations.
- **Dockerfile**: Instructions to build the application image.
- **src/**: Application source code.

## Useful Commands

- **Start the containers**: `docker-compose up`
- **Stop the containers**: `docker-compose down`
- **Rebuild the containers**: `docker-compose up --build`
- **View running containers**: `docker ps`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).