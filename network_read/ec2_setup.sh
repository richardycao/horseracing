sudo yum install git -y

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

sudo yum -y install python-pip
pip3 install numpy pandas requests boto3

git clone https://github.com/richardycao/horseracing.git

export AWS_ACCESS_KEY=
export AWS_SECRET_ACCESS_KEY=