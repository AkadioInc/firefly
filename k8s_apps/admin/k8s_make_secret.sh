# create kubernetes secret for HSDS password for firefly admin
if [ $# -eq 0 ] || ([ $1 == "-h" ] || [ $1 == "--help" ]); then
   echo "Usage: k9s_make_secret.sh <firefly_admin_password?"
   exit 1
fi

FIREFLY_ADMIN_PASSWORD=$1
echo $FIREFLY_ADMIN_PASSWORD

echo -n firefly_admin > /tmp/hs_username
echo -n ${FIREFLY_ADMIN_PASSWORD} > /tmp/hs_password

# create the secret
kubectl create secret generic hsds-firefly-admin-pswd --from-file=/tmp/hs_username --from-file=/tmp/hs_password

# delete the temp files
rm /tmp/hs_username
rm /tmp/hs_password
