# Use the base image specified in the docker-compose.yaml
FROM opea/gpt-sovits:latest

# Set the working directory
WORKDIR /home/user/GPT-SoVITS

# Remove LangSegment
RUN sed -i 's/^import LangSegment/#import LangSegment/g' /home/user/GPT-SoVITS/api.py && \
    sed -i 's/^from LangSegment/#from LangSegment/g' /home/user/GPT-SoVITS/api.py && \
    sed -i 's/LangSegment.classify/# LangSegment.classify/g' /home/user/GPT-SoVITS/api.py && \
    sed -i 's/LangSegment.setLangfilters/# LangSegment.setLangfilters/g' /home/user/GPT-SoVITS/api.py

# Command to run the application
# CMD ["python", "api.py"]
