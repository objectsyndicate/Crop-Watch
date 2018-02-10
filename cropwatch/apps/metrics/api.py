from rest_framework import parsers, renderers
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from cropwatch.apps.metrics.models import *

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import activate
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from cropwatch.apps.metrics.permissions import IsBot
from cropwatch.apps.metrics.tasks import *



# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# we override the default auth because there is no throttle. 
# using anon throttle
class ObtainAuthToken(APIView):
    throttle_classes = (AnonRateThrottle,)
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


obtain_auth_token = ObtainAuthToken.as_view()



def is_night(now, start, end):
    if start <= end:
        return start <= now < end
    else:  # over midnight e.g., 23:30-04:15
        return start <= now or now < end


class ioTankSerializer(serializers.ModelSerializer):
    class Meta:
        model = ioTank
        fields = ['bot']


class iotv1Serializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = ['t1', 't2', 'h', 'uv', 'l']


class ioTankAddSerializer(serializers.Serializer):
    add = serializers.CharField(max_length=5)

    def validate_add(self, value):
        """
        Check that the blog post is about Django.
        """
        if 'true' not in value.lower():
            raise serializers.ValidationError("add not true")
        return value


class ioTankDeleteSerializer(serializers.Serializer):
    delete = serializers.CharField(max_length=5)
    uuid = serializers.UUIDField()

    def validate_delete(self, value):
        """
        Check that the blog post is about Django.
        """
        if 'true' not in value.lower():
            raise serializers.ValidationError("delete not true")
        return value


class ioTankListSerializer(serializers.Serializer):
    list_tokens = serializers.CharField(max_length=5)

    def validate_list_tokens(self, value):
        """
        Check that the blog post is about Django.
        """
        if 'true' not in value.lower():
            raise serializers.ValidationError("list_tokens not true")
        return value


@api_view(['POST'])
@permission_classes((IsBot,))
def v1_ioTank_add(request):
    if request.method == 'POST':
        serializer = ioTankAddSerializer(data=request.data)
        if serializer.is_valid():
            try:
                newio = ioTank(owner=request.user)
                user = User.objects.create_user(str(newio)[:30])
                newio.bot_user_id = user.id
                newio.save()
                Token.objects.get_or_create(user=user)
                return Response(timezone.now(), status=status.HTTP_201_CREATED)
            except:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsBot,))
def v1_ioTank_delete(request):
    if request.method == 'POST':
        serializer = ioTankDeleteSerializer(data=request.data)
        if serializer.is_valid():
            uuid = serializer.validated_data.get('uuid')

            return Response(timezone.now(), status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsBot,))
def v1_ioTank_list(request):
    if request.method == 'POST':
        serializer = ioTankListSerializer(data=request.data)
        if serializer.is_valid():
            bots = ioTank.objects.filter(owner=request.user)
            out = {}

            for b in bots:
                token = Token.objects.get(user=b.bot_user)
                out[str(b.id)] = str(token)

            return Response(out, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsBot,))
def v1_iot(request):
    if request.method == 'POST':
        serializer = iotv1Serializer(data=request.data)
        if serializer.is_valid():
            try:
                bot = ioTank.objects.get(bot_user=request.user)
                t1 = serializer.validated_data.get('t1')
                t2 = serializer.validated_data.get('t2')
                h = serializer.validated_data.get('h')
                uv = serializer.validated_data.get('uv')
                l = serializer.validated_data.get('l')

                owner = bot.owner
                settings = AccountSettings.objects.get(user=owner)
                serializer.save(bot=ioTank.objects.get(bot_user=request.user), t1=t1, t2=t2, h=h, uv=uv, l=l)
                activate(settings.timezone)
                sub = "Crop🌱Watch Notice"
                red_flags = []

                if bot.u == 'F':
                    t1 = 9 / 5 * int(t1) + 32
                    t2 = 9 / 5 * int(t2) + 32

                def send(flag_list):
                    if bot.name is "":
                        bot.name = str(bot.id)

                    if bot.name is None:
                        bot.name = str(bot.id)

                    s = ", ".join(flag_list)
                    msg = "ioTank '" + bot.name + "' has the following notices: " + s + ". \n" + "T1:" + str(
                        int(t1)) + "º" + bot.u + " T2:" + str(t2) + "º" + bot.u + " H:" + str(h) + "% UVI:" + str(
                        uv) + " Lux:" + str(l) + " \n"
                    if settings.notify_iotank_emergency is True:

                        # Send E-mail
                        if settings.notify_email is True and settings.email_daily > 0:
                            send_email.apply_async((sub, msg, settings.user.email, owner.id))

                # Check max temp 1
                if bot.x < t1:
                    red_flags.append("Temp 1 above maximum")

                # check min temp 1
                if bot.m > t1:
                    red_flags.append("Temp 1 under minimum")

                # Check max temp 2
                if bot.x2 < t2:
                    red_flags.append("Temp 2 above maximum")

                # check min temp 2
                if bot.m2 > t2:
                    red_flags.append("Temp 2 under minimum")

                # check humidity
                if bot.mh > h or bot.xh < h:
                    red_flags.append("Humidity out of range")

                # now
                now = timezone.localtime(timezone.now()).time()

                # nighttime, too bright?
                if is_night(now, bot.night_start, bot.night_end) == True and l > bot.night_max_light:
                    red_flags.append("It is too bright for the dark cycle")

                # daytime, not bright enough?
                if is_night(now, bot.night_start, bot.night_end) == False and l < bot.day_min_light:
                    red_flags.append("It is not bright enough for the light cycle")
                send(red_flags)

                return Response(timezone.now(), status=status.HTTP_201_CREATED)
            except ObjectDoesNotExist:
                return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
